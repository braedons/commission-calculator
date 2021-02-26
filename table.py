import tkinter as tk

class Table:
	'''Creates a table for Tkinter using labels'''

	def __init__(self, master, nrows, ncols, colwidth, padx=2, pady=2):
		self.master = master
		self.nrows = nrows
		self.ncols = ncols
		self.colwidth = colwidth

		self.tbl = tk.Frame(master=master)
		self.labels = []

		for r in range(nrows):
			row = []
			for c in range(ncols):
				row.append(tk.Label(self.tbl))
				row[-1].grid(row=r, column=c, padx=padx, pady=pady)

			self.labels.append(row)
	
	def set(self, rc, index, *args):
		'''Sets a row or column of labels to the values provided in args

		Inputs:
		rc -- 'row' or 'col', indicates whether to iterate along a row or col
		index -- (r,c), starting index for iteration
		args -- x,y,z... The values to insert while iterating

		Outputs:
		None
		'''
		if rc == 'row':
			c = index[1]
			for arg in args:
				if c >= self.ncols: break

				self.labels[index[0]][c]['text'] = arg
				c += 1
		elif rc == 'col':
			r = index[0]
			for arg in args:
				if r >= self.nrows: break

				self.labels[r][index[1]]['text'] = arg
				r += 1
		else: raise ValueError('rc must equal "row" or "col"')

	def set_colours(self, rc, index, fg, bg):
		if rc == 'row':
			for c in range(index[1], self.ncols):
				self.labels[index[0]][c].config(fg=fg)
				self.labels[index[0]][c].config(bg=bg)
		elif rc == 'col':
			for r in range(index[0], self.nrows):
				self.labels[r][index[1]].config(fg=fg)
				self.labels[r][index[1]].config(bg=bg)
		else: raise ValueError('rc must equal "row" or "col"')

	def pack(self):
		self.tbl.pack()
