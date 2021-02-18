import tkinter as tk

COMMISSION_RATES = [.06, .03, .015]
OUT_OF_DEPT_RATE = .01
REPLACEMENT_PLAN_RATE = .1


class PersonalStats:
	def __init__(self):
		self.bucket_totals = [0,0,0]
		self.seen_custs = set()
	
	def clear(self):
		self = PersonalStats()

def get_commission_bucket(unit_price):
	if unit_price < 0: raise ValueError('UNIT PRICE MUST BE NON-NEGATIVE')
	elif unit_price < 10: return 0
	elif unit_price < 100: return 1
	else: return 2

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

def calc_commission(table, stats):
	# Calculate commissions, 3 buckets
	# item = [Transaction Number, Sale Type, Line, Sku, Description, Qty, Unit Price, Total]
	for item in table:
		# Format differs for sale and exchange transactions
		if item[1] == 'sale':
			unit_price, total = float(item[-2][1:]), float(item[-1][1:])
			bucket_index = get_commission_bucket(unit_price)
			stats.bucket_totals[bucket_index] += total # TODO: does (total == qty*unit_price)?
	
	# Multiplies corresponding rates and bucket_totals
	total_commission = sum([total*rate for total, rate in zip(stats.bucket_totals, COMMISSION_RATES)])

	return total_commission

def count_customers(table, stats):
	for transaction in table:
		stats.seen_custs.add(transaction[0])
	
	return len(stats.seen_custs)

def update_commission(text_in, commission_lbl, cust_lbl, stats):
	table = parse_table(text_in)
	commission = calc_commission(table, stats)
	n_custs = count_customers(table, stats)

	commission_lbl['text'] = 'Total Commission: $' + str(round(commission, 2))
	cust_lbl['text'] = 'Customers Helped: ' + str(n_custs)

def clear(transactions_txt, commission_lbl, cust_lbl, stats):
	transactions_txt.delete('1.0', 'end')
	commission_lbl['text'] = ''
	cust_lbl['text'] = ''

	stats.clear()

if __name__ == '__main__':
	window = tk.Tk()
	stats = PersonalStats()
	
	instr = tk.Label(text='Enter the copied transaction records')
	transactions_txt = tk.Text()
	commission_lbl = tk.Label()
	cust_lbl = tk.Label()

	# Results should be saved and added together between process clicks until cleared
	bucket_totals = [0,0,0]
	
	btn_frame = tk.Frame(master=window)
	proc_btn = tk.Button(text='Process', master=btn_frame, command=lambda: update_commission(transactions_txt, commission_lbl, cust_lbl, stats))
	clear_btn = tk.Button(text='Clear', master=btn_frame, command=lambda: clear(transactions_txt, commission_lbl, cust_lbl, stats))

	proc_btn.pack(side=tk.LEFT)
	clear_btn.pack(side=tk.LEFT)

	# Pack all widgets
	instr.pack()
	transactions_txt.pack()

	btn_frame.pack()
	commission_lbl.pack()
	cust_lbl.pack()

	# Start running app
	window.mainloop()
