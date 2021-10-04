import tkinter as tk
import tkinter.messagebox
from table import Table
from math import inf
from sys import exc_info

COMMISSION_RATES = (.06, .03, .015)
COMMISSION_RANGES = ((0, 9.99), (10, 99.99), (100, inf))
OUT_OF_DEPT_RATE = .01
SERVICE_PLAN_RATE = .1

BUCKET_BREAKDOWN_COLS = ['6% Bracket', '3% Bracket', '1.5% Bracket', 'Out of Dept', 'Service Plans']
BUCKET_BREAKDOWN_ROWS = ('Commission', 'Sales', '% Total Sales')


class PersonalStats:
	def __init__(self):
		self.bucket_totals = [0] * len(COMMISSION_RATES)
		self.service_plan_total = 0
		self.out_of_dept_total = 0
		self.seen_custs = set()
		self.deductions = [0] * len(COMMISSION_RATES)
		self.prev_table = None

		self.returns_count = 0
		self.returns_totals = [0] * len(COMMISSION_RATES)
	
	def clear(self):
		self.__init__()

	# ----------------------------------------- Commission calculations
	def calc_bucket_commissions(self):
		bucket_totals = [total - deduction for total, deduction in zip(self.bucket_totals, self.deductions)]
		return [total*rate for total, rate in zip(bucket_totals, COMMISSION_RATES)]

	def calc_out_of_dept_commission(self):
		return self.out_of_dept_total * OUT_OF_DEPT_RATE

	def calc_service_plan_commission(self):
		return self.service_plan_total*SERVICE_PLAN_RATE

	def calc_returns_stats(self):
		return sum([total*rate for total, rate in zip(self.returns_totals, COMMISSION_RATES)]), sum(self.returns_totals)

	def calculate_commission(self):
		commission = sum(self.calc_bucket_commissions()) \
				+ self.calc_out_of_dept_commission() \
				+ self.calc_service_plan_commission()
		sales_total = sum(self.bucket_totals) + self.service_plan_total

		return commission, sales_total

def get_commission_bucket(unit_price):
	if unit_price < 0: raise ValueError('UNIT PRICE MUST BE NON-NEGATIVE')

	for i in range(1, len(COMMISSION_RANGES)):
		if unit_price < COMMISSION_RANGES[i][0]: return i-1

	return len(COMMISSION_RANGES)-1

def parse_table(text_in):
	contents = [line.strip().lower() for line in text_in.get('1.0', 'end-1c').split('\n')]

	# Find start of table
	for i in range(len(contents)):
		if contents[i] == 'total' and contents[i+1][:8] == 'total: $': break
	
	i += 2

	# Parse table, filter out junk
	# TODO: make more thorough
	table = [line.split('\t') for line in contents[i:]]
	table = [line for line in table if len(line) == 8]
	return table

def is_service_plan(description):
	split = description.split()

	return split[0].isdigit() and split[1] == 'year' and split[-1] == 'plan'

def calc_commission(table, deductions_ents, stats):
	if table != stats.prev_table:
		# Calculate commissions, 3 buckets
		# item = [Transaction Number, Sale Type, Line, Sku, Description, Qty, Unit Price, Total]
		for item in table:
			# Format differs for sale and exchange transactions
			if item[1] == 'sale':
				unit_price, total = float(item[-2][1:].replace(',', '')), float(item[-1][1:].replace(',', ''))

				# Service plans have different rates
				if is_service_plan(item[4]):
					stats.service_plan_total += total
				else:
					bucket_index = get_commission_bucket(unit_price)
					stats.bucket_totals[bucket_index] += total # TODO: does (total == qty*unit_price)?
			elif item[1] == 'exchange':
				total = float(item[-1][2:-1].replace(',', '')) # TODO: verify total is ok, qty doesn't matter
				bucket_index = get_commission_bucket(total)
				stats.bucket_totals[bucket_index] += total
			elif item[1] == 'return':
				total = float(item[-1][2:-1].replace(',', '')) # TODO: verify total is ok, qty doesn't matter
				bucket_index = get_commission_bucket(total)
				stats.returns_count += 1 # TODO: add 1 or actual count of returned
				stats.returns_totals[bucket_index] += total

		stats.prev_table = table
	
	# Handle specified deductions
	stats.out_of_dept_total = 0

	for i in range(len(stats.bucket_totals)):
		# TODO: what about negatives?
		# TODO: handle malformed input
		ent = deductions_ents[i].get()
		if ent:
			ent = float(ent.replace(',', ''))
			stats.deductions[i] = ent
			stats.out_of_dept_total += ent
	
	# Multiplies corresponding rates and bucket_totals
	total_commission, sales_total = stats.calculate_commission()

	return total_commission, sales_total

def count_customers(table, stats):
	for transaction in table:
		stats.seen_custs.add(transaction[0])
	
	return len(stats.seen_custs)

def update_results(text_in, deductions_ents, results_lbls, returns_lbls, bucket_breakdown_tbl, stats):
	try:
		table = parse_table(text_in)
		commission, sales_total = calc_commission(table, deductions_ents, stats)
		n_custs = count_customers(table, stats)
		returns_commission_lost, returns_total = stats.calc_returns_stats()

		results_lbls['commission_lbl']['text'] = 'Total Commission: $' + str(round(commission, 2))
		results_lbls['cust_lbl']['text'] = 'Customers Helped: ' + str(n_custs)
		results_lbls['sales_lbl']['text'] = 'Total Sales: $' + str(round(sales_total, 2))
		results_lbls['overall_rate_lbl']['text'] = 'Commission Rate: ' + (str(round(commission / sales_total * 100, 2)) if sales_total else '0') + '%' # Handles divide by 0 error

		returns_lbls['count']['text'] = f'Returns Count: {stats.returns_count}'
		returns_lbls['total']['text'] = f'Returns Total: ${returns_total}'
		returns_lbls['commission']['text']  = f'Returns Commission Lost: ${round(returns_commission_lost, 2)}'

		# Update breakdown table
		# Commission row
		bucket_commissions = stats.calc_bucket_commissions()
		for i in range(3): bucket_breakdown_tbl.set('row', (1,i+1), f'${round(bucket_commissions[i], 2)}')
		bucket_breakdown_tbl.set('row', (1,4), f'${round(stats.calc_out_of_dept_commission(), 2)}')
		bucket_breakdown_tbl.set('row', (1,5), f'${round(stats.calc_service_plan_commission(), 2)}')

		# Sales row
		for i in range(3): bucket_breakdown_tbl.set('row', (2,i+1), f'${round(stats.bucket_totals[i], 2)}')
		bucket_breakdown_tbl.set('row', (2,4), f'${round(stats.out_of_dept_total, 2)}')
		bucket_breakdown_tbl.set('row', (2,5), f'${round(stats.service_plan_total, 2)}')

		# % total sales row
		for i in range(3): bucket_breakdown_tbl.set('row', (3,i+1), f'{(round(stats.bucket_totals[i] / sales_total * 100, 2) if sales_total else 0)}%')
		bucket_breakdown_tbl.set('row', (3,4), f'{(round(stats.out_of_dept_total / sales_total * 100, 2) if sales_total else 0)}%')
		bucket_breakdown_tbl.set('row', (3,5), f'{(round(stats.service_plan_total / sales_total * 100, 2) if sales_total else 0)}%')
	except Exception as e:
		print_exception(e)

def clear(transactions_txt, deductions_ents, results_lbls, returns_lbls, bucket_breakdown_tbl, stats):
	try:
		transactions_txt.delete('1.0', 'end')
		for ent in deductions_ents: ent.delete(0, 'end')
		for lbl in results_lbls.values(): lbl['text'] = ''
		for lbl in returns_lbls.values(): lbl['text'] = ''

		# TODO: clear table
		for r in range(1, len(BUCKET_BREAKDOWN_ROWS)+1): bucket_breakdown_tbl.set(f'row', (r,1), *[''] * len(BUCKET_BREAKDOWN_COLS))

		stats.clear()
	except Exception as e:
		print_exception(e)

def paste_page(transactions_txt, window):
	transactions_txt.delete('1.0', 'end')
	
	try:
		clipboard = window.clipboard_get()
	except:
		clipboard = ''
	transactions_txt.insert('end', clipboard)

def print_exception(e):
	exception_type, exception_object, exception_traceback = exc_info()
	filename = exception_traceback.tb_frame.f_code.co_filename
	line_number = exception_traceback.tb_lineno
	tk.messagebox.showerror('Error', f'{exception_type} error in {filename}:{line_number}\n\n{e}')

# ----------------------------------------------------------- Event Callbacks

def paste_clipboard(event, window):
	if event.widget.compare("end-1c", "==", "1.0"):
		event.widget.delete(1.0, "end")

		try:
			clipboard = window.clipboard_get()
		except:
			clipboard = ''
		transactions_txt.insert('end', clipboard)

def select_all(event):
	event.widget.tag_add('sel', "1.0", 'end')
	event.widget.mark_set('insert', "1.0")
	event.widget.see('insert')

# ----------------------------------------------------------- Main

if __name__ == '__main__':
	window = tk.Tk()
	window.title('GSA')
	stats = PersonalStats()
	
	instr = tk.Label(text='Enter the copied transaction records')
	transactions_txt = tk.Text()
	transactions_txt.bind('<1>', lambda ev: paste_clipboard(ev, window))
	transactions_txt.bind('<Control-KeyRelease-a>', select_all)

	# Out of dept deductions section
	deductions_frame = tk.Frame(master=window)
	tk.Label(text='Enter the amount of out of department sales to deduct from each range', master=deductions_frame).pack()
	deductions_ents = [None] * 3
	for i in range(3):
		curr = tk.Frame(master=deductions_frame)
		lbl = tk.Label(text=f'${COMMISSION_RANGES[i][0]}-${COMMISSION_RANGES[i][1]}:', master=curr)
		ent = tk.Entry(master=curr)

		lbl.pack(side=tk.LEFT)
		ent.pack(side=tk.LEFT)
		curr.pack()

		deductions_ents[i] = ent

	# Build results section
	result_lbls_frame = tk.Frame()

	results_frame = tk.Frame(master=result_lbls_frame)
	results_lbls = {}

	results_lbls['commission_lbl'] = tk.Label(master=results_frame)
	results_lbls['cust_lbl'] = tk.Label(master=results_frame)
	results_lbls['sales_lbl'] = tk.Label(master=results_frame)
	results_lbls['overall_rate_lbl'] = tk.Label(master=results_frame)
	
	for lbl in results_lbls.values(): lbl.pack()
	results_frame.pack(side=tk.LEFT, padx=20)

	# Build returns section
	returns_frame = tk.Frame(master=result_lbls_frame)
	returns_lbls = {}

	returns_lbls['count'] = tk.Label(master=returns_frame)
	returns_lbls['total'] = tk.Label(master=returns_frame)
	returns_lbls['commission'] = tk.Label(master=returns_frame)
	
	for lbl in returns_lbls.values(): lbl.pack()
	returns_frame.pack(side=tk.LEFT, padx=20)

	# Creating results table broken down by bucket
	bucket_breakdown_tbl = Table(master=window, ncols=len(BUCKET_BREAKDOWN_COLS)+1, nrows=len(BUCKET_BREAKDOWN_ROWS)+1, colwidth=12)

	bucket_breakdown_tbl.set('row', (0,1), *BUCKET_BREAKDOWN_COLS)
	bucket_breakdown_tbl.set('col', (1,0), *BUCKET_BREAKDOWN_ROWS)

	bucket_breakdown_tbl.set_colours('row', (0,1), 'white', 'grey')
	bucket_breakdown_tbl.set_colours('col', (1,0), 'white', 'grey')

	# Results should be saved and added together between process clicks until cleared
	bucket_totals = [0,0,0]
	
	btn_frame = tk.Frame(master=window)
	paste_page_btn = tk.Button(text='Paste New Page', master=btn_frame, command=lambda: paste_page(transactions_txt, window))
	proc_btn = tk.Button(text='Process', master=btn_frame, command=lambda: update_results(transactions_txt, deductions_ents, results_lbls, returns_lbls, bucket_breakdown_tbl, stats))
	clear_btn = tk.Button(text='Clear', master=btn_frame, command=lambda: clear(transactions_txt, deductions_ents, results_lbls, returns_lbls, bucket_breakdown_tbl, stats))

	paste_page_btn.pack(side=tk.LEFT)
	proc_btn.pack(side=tk.LEFT)
	clear_btn.pack(side=tk.LEFT)

	# Pack all widgets
	instr.pack()
	transactions_txt.pack()

	deductions_frame.pack()

	btn_frame.pack()
	result_lbls_frame.pack()
	bucket_breakdown_tbl.pack()

	# Start running app
	window.mainloop()

