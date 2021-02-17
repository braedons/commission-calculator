import tkinter as tk

COMMISSION_RATES = [.06, .03, .015]
OUT_OF_DEPT_RATE = .01
REPLACEMENT_PLAN_RATE = .1

def get_commission_bucket(unit_price):
	if unit_price < 0: raise ValueError('UNIT PRICE MUST BE NON-NEGATIVE')
	elif unit_price < 10: return 0
	elif unit_price < 100: return 1
	else: return 2

def calc_commission(text_in, bucket_totals):
	contents = [line.strip().lower() for line in text_in.get('1.0', 'end-1c').split('\n')]

	# Find start of table
	for i in range(len(contents)):
		if contents[i] == 'total' and contents[i+1][:8] == 'total: $': break
	
	i += 2

	# Parse table, filter out junk
	# TODO: make more thorough
	table = [line.split('\t') for line in contents[i:]]
	table = [line for line in table if len(line) == 8]

	# Calculate commissions, 3 buckets
	# item = [Transaction Number, Sale Type, Line, Sku, Description, Qty, Unit Price, Total]
	for item in table:
		# Format differs for sale and exchange transactions
		if item[1] == 'sale':
			unit_price, total = float(item[-2][1:]), float(item[-1][1:])
			bucket_index = get_commission_bucket(unit_price)
			bucket_totals[bucket_index] += total # TODO: does (total == qty*unit_price)?
	
	# Multiplies corresponding rates and bucket_totals
	total_commission = sum([total*rate for total, rate in zip(bucket_totals, COMMISSION_RATES)])

	return total_commission

def update_commission(text_in, text_out, bucket_totals):
	commission = calc_commission(text_in, bucket_totals)
	text_out['text'] = 'Total Commission: $' + str(round(commission, 2))

def clear(records, results_label, bucket_totals):
	records.delete('1.0', 'end')
	results_label['text'] = ''

	# Reset bucket_totals, can't just reassign to new array
	for i in range(len(bucket_totals)): bucket_totals[i] = 0

if __name__ == '__main__':
	window = tk.Tk()
	
	instr = tk.Label(text='Enter the copied transaction records')
	records = tk.Text()
	results_label = tk.Label()

	# Results should be saved and added together between process clicks until cleared
	bucket_totals = [0,0,0]
	
	btn_frame = tk.Frame(master=window)
	proc_btn = tk.Button(text='Process', master=btn_frame, command=lambda: update_commission(records, results_label, bucket_totals))
	clear_btn = tk.Button(text='Clear', master=btn_frame, command=lambda: clear(records, results_label, bucket_totals))

	proc_btn.pack(side=tk.LEFT)
	clear_btn.pack(side=tk.LEFT)

	# Pack all widgets
	instr.pack()
	records.pack()

	btn_frame.pack()
	results_label.pack()

	# Start running app
	window.mainloop()
