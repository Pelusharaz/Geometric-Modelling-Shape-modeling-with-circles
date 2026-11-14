import json, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from geometry.primitives import Circle, Point
from modeling.factory import ModelingFactory
from ui.canvas import ModelingCanvas

BG='#0b1220'; PANEL='#111c2e'; TEXT='#e5edf7'; MUTED='#91a4bb'; ACCENT='#28b9ad'
class CircleModeller(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Circle Shape Modeller | Geometric Modelling'); self.geometry('1320x820'); self.minsize(1000,650); self.configure(bg=BG)
        self.circles=[]; self.shape=None; self.selected_id=None; self.next_id=1; self.history=[]; self.redo_stack=[]
        self.tool=tk.StringVar(value='Select Circle'); self.method=tk.StringVar(value='Hermite Circle Envelope'); self.resolution=tk.IntVar(value=100)
        self.show_centerline=tk.BooleanVar(value=True); self.show_contacts=tk.BooleanVar(value=True); self.show_tangents=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value='Ready. Choose Add Circle and click twice to place a circle.')
        self._build(); self.push_history()
        self.bind('<Delete>',lambda e:self.delete_selected()); self.bind('<Control-z>',lambda e:self.undo()); self.bind('<Control-y>',lambda e:self.redo())
    def _build(self):
        top=tk.Frame(self,bg=BG); top.pack(fill='x',padx=18,pady=(14,10))
        tk.Label(top,text='CIRCLE SHAPE MODELLER',bg=BG,fg=TEXT,font=('Segoe UI',17,'bold')).pack(side='left')
        tk.Label(top,text='GEOMETRIC MODELLING LAB',bg=BG,fg=ACCENT,font=('Segoe UI',9,'bold')).pack(side='right')
        body=tk.Frame(self,bg=BG); body.pack(fill='both',expand=True,padx=14,pady=5)
        sidebar=tk.Frame(body,bg=PANEL,width=270); sidebar.pack(side='left',fill='y',padx=(0,10)); sidebar.pack_propagate(False)
        side_canvas=tk.Canvas(sidebar,bg=PANEL,width=255,highlightthickness=0)
        scrollbar=ttk.Scrollbar(sidebar,orient='vertical',command=side_canvas.yview)
        side_canvas.configure(yscrollcommand=scrollbar.set)
        side_canvas.pack(side='left',fill='both',expand=True)
        scrollbar.pack(side='right',fill='y')
        side=tk.Frame(side_canvas,bg=PANEL)
        side_window=side_canvas.create_window((0,0),window=side,anchor='nw')
        side.bind('<Configure>',lambda e:side_canvas.configure(scrollregion=side_canvas.bbox('all')))
        side_canvas.bind('<Configure>',lambda e:side_canvas.itemconfigure(side_window,width=e.width))
        def scroll_sidebar(event):
            x=side_canvas.winfo_rootx(); y=side_canvas.winfo_rooty()
            if not (x<=event.x_root<x+side_canvas.winfo_width() and y<=event.y_root<y+side_canvas.winfo_height()):
                return
            if getattr(event,'num',None)==4: side_canvas.yview_scroll(-1,'units')
            elif getattr(event,'num',None)==5: side_canvas.yview_scroll(1,'units')
            elif event.delta:
                units=int(-event.delta/120)
                side_canvas.yview_scroll(units if units else (-1 if event.delta>0 else 1),'units')
            return 'break'
        self.bind_all('<MouseWheel>',scroll_sidebar)
        self.bind_all('<Button-4>',scroll_sidebar)
        self.bind_all('<Button-5>',scroll_sidebar)
        self._section(side,'TOOLS')
        for label in ['Select Circle','Add Circle']:
            ttk.Radiobutton(side,text=label,value=label,variable=self.tool).pack(anchor='w',padx=16,pady=4)
        self._button(side,'Delete selected',self.delete_selected); self._button(side,'Clear all circles',self.clear_circles)
        row=tk.Frame(side,bg=PANEL); row.pack(fill='x',padx=12,pady=3)
        self._button(row,'Undo',self.undo,small=True); self._button(row,'Redo',self.redo,small=True)
        self._section(side,'SELECTED CIRCLE')
        self.id_label=tk.Label(side,text='None selected',bg=PANEL,fg=MUTED); self.id_label.pack(anchor='w',padx=16,pady=(0,6))
        self.x_var=tk.StringVar(); self.y_var=tk.StringVar(); self.r_var=tk.StringVar()
        for label,var in [('Center X',self.x_var),('Center Y',self.y_var),('Radius',self.r_var)]:
            tk.Label(side,text=label,bg=PANEL,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=16)
            ent=ttk.Entry(side,textvariable=var); ent.pack(fill='x',padx=14,pady=(2,6))
        self._button(side,'Apply parameters',self.apply_parameters)
        self._section(side,'MODELLING')
        ttk.Combobox(side,textvariable=self.method,values=ModelingFactory.names(),state='readonly').pack(fill='x',padx=14,pady=5)
        tk.Label(side,text='Curve resolution',bg=PANEL,fg=MUTED).pack(anchor='w',padx=16,pady=(8,0))
        ttk.Scale(side,from_=20,to=240,variable=self.resolution,orient='horizontal').pack(fill='x',padx=14,pady=5)
        self._button(side,'Generate shape',self.generate,primary=True)
        self._button(side,'Fit view',lambda:self.canvas.fit_view())
        self._section(side,'DISPLAY LAYERS')
        for label,var in [('Show centreline',self.show_centerline),('Show contact points',self.show_contacts),('Show tangent vectors',self.show_tangents)]:
            ttk.Checkbutton(side,text=label,variable=var,command=lambda:self.canvas.redraw()).pack(anchor='w',padx=15,pady=3)
        self._section(side,'PROJECT')
        row2=tk.Frame(side,bg=PANEL); row2.pack(fill='x',padx=10,pady=3)
        self._button(row2,'Open',self.open_project,small=True); self._button(row2,'Save',self.save_project,small=True)
        tk.Label(side,text='Tip: drag a circle to move it. Drag near its edge to resize.',wraplength=230,justify='left',bg=PANEL,fg=MUTED,font=('Segoe UI',8)).pack(anchor='w',padx=15,pady=12)
        self.canvas=ModelingCanvas(body,self); self.canvas.pack(side='left',fill='both',expand=True)
        bottom=tk.Frame(self,bg='#0f1a2b'); bottom.pack(fill='x',side='bottom')
        tk.Label(bottom,textvariable=self.status,bg='#0f1a2b',fg='#a9bacd',anchor='w',padx=14,pady=8).pack(fill='x')
        style=ttk.Style(); style.theme_use('clam'); style.configure('TEntry',fieldbackground='#1b2a40',foreground=TEXT,bordercolor='#33445d'); style.configure('TCombobox',fieldbackground='#1b2a40',foreground=TEXT); style.map('TCombobox',fieldbackground=[('readonly','#1b2a40')],foreground=[('readonly',TEXT)])
        style.configure('TRadiobutton',background=PANEL,foreground=TEXT); style.map('TRadiobutton',background=[('active',PANEL)],foreground=[('active',TEXT)])
        style.configure('TCheckbutton',background=PANEL,foreground=TEXT); style.map('TCheckbutton',background=[('active',PANEL)],foreground=[('active',TEXT)])
        style.configure('Horizontal.TScale',background=PANEL,troughcolor='#26364c')
    def _section(self,parent,title): tk.Label(parent,text=title,bg=PANEL,fg=ACCENT,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=14,pady=(15,7))
    def _button(self,parent,label,command,primary=False,small=False):
        b=tk.Button(parent,text=label,command=command,bg=ACCENT if primary else '#203149',fg='#07131d' if primary else TEXT,activebackground='#39d0c3',activeforeground='#07131d',relief='flat',bd=0,padx=10,pady=6 if not small else 4,font=('Segoe UI',9,'bold' if primary else 'normal'),cursor='hand2')
        b.pack(side='left' if small else 'top',fill='x' if not small else 'x',expand=small,padx=4 if small else 13,pady=3); return b
    def set_status(self,msg): self.status.set(msg)
    def selected_circle(self): return next((c for c in self.circles if c.id==self.selected_id),None)
    def add_circle(self,center,r):
        self.circles.append(Circle(self.next_id,center,r)); self.selected_id=self.next_id; self.next_id+=1; self.shape=None; self.push_history(); self.update_circle_fields(); self.set_status(f'Circle {self.selected_id} added. Creation order is preserved.')
    def select_circle(self,cid): self.selected_id=cid; self.update_circle_fields()
    def update_circle_fields(self):
        c=self.selected_circle(); self.id_label.config(text=f'Circle ID: {c.id}' if c else 'None selected')
        for var,val in [(self.x_var,c.center.x if c else ''),(self.y_var,c.center.y if c else ''),(self.r_var,c.radius if c else '')]: var.set(f'{val:.2f}' if isinstance(val,(int,float)) else val)
    def apply_parameters(self):
        c=self.selected_circle()
        if not c: self.set_status('Select a circle first.'); return
        try:
            x,y,r=float(self.x_var.get()),float(self.y_var.get()),float(self.r_var.get())
            if r<=0: raise ValueError('Radius must be greater than zero.')
            c.center=Point(x,y); c.radius=r; self.shape=None; self.push_history(); self.canvas.redraw(); self.set_status('Circle parameters updated.')
        except ValueError as e: messagebox.showerror('Invalid parameters',str(e))
    def delete_selected(self):
        if self.selected_id is None:return
        self.circles=[c for c in self.circles if c.id!=self.selected_id]; self.selected_id=None; self.shape=None; self.push_history(); self.update_circle_fields(); self.canvas.redraw(); self.set_status('Selected circle deleted.')
    def clear_circles(self):
        if not self.circles:return
        if messagebox.askyesno('Clear canvas','Remove all circles and the generated shape?'):
            self.circles=[]; self.selected_id=None; self.shape=None; self.push_history(); self.update_circle_fields(); self.canvas.redraw(); self.set_status('Canvas cleared.')
    def generate(self):
        try:
            self.shape=ModelingFactory.create(self.method.get()).generate(self.circles,max(20,int(self.resolution.get())))
            self.canvas.redraw(); msg=f'{self.method.get()} generated successfully.'
            if self.shape.warnings: msg+='  '+self.shape.warnings[0]
            self.set_status(msg)
            if self.shape.warnings: messagebox.showwarning('Geometry warnings','\n\n'.join(self.shape.warnings))
        except Exception as e: messagebox.showerror('Cannot generate shape',str(e)); self.set_status(str(e))
    def push_history(self):
        snap=[(c.id,c.center.x,c.center.y,c.radius) for c in self.circles]
        if self.history and self.history[-1]==snap:return
        self.history.append(snap); self.history=self.history[-50:]; self.redo_stack=[]
    def restore(self,snap):
        self.circles=[Circle(i,Point(x,y),r) for i,x,y,r in snap]; self.next_id=max([c.id for c in self.circles],default=0)+1
        if self.selected_id not in [c.id for c in self.circles]:self.selected_id=None
        self.shape=None; self.update_circle_fields(); self.canvas.redraw()
    def undo(self):
        if len(self.history)<2:return
        self.redo_stack.append(self.history.pop()); self.restore(self.history[-1]); self.set_status('Undo completed.')
    def redo(self):
        if not self.redo_stack:return
        snap=self.redo_stack.pop(); self.history.append(snap); self.restore(snap); self.set_status('Redo completed.')
    def save_project(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Circle modeller project','*.json')])
        if not path:return
        data={'version':1,'method':self.method.get(),'resolution':self.resolution.get(),'circles':[{'id':c.id,'x':c.center.x,'y':c.center.y,'radius':c.radius} for c in self.circles]}
        with open(path,'w',encoding='utf-8') as f:json.dump(data,f,indent=2)
        self.set_status('Project saved.')
    def open_project(self):
        path=filedialog.askopenfilename(filetypes=[('Circle modeller project','*.json')])
        if not path:return
        try:
            data=json.load(open(path,encoding='utf-8')); self.circles=[Circle(int(c['id']),Point(float(c['x']),float(c['y'])),float(c['radius'])) for c in data['circles']]
            if any(c.radius<=0 for c in self.circles):raise ValueError('Project contains a non-positive radius.')
            self.next_id=max([c.id for c in self.circles],default=0)+1; self.method.set(data.get('method',ModelingFactory.names()[0])); self.resolution.set(data.get('resolution',100))
            self.shape=None; self.selected_id=None; self.push_history(); self.update_circle_fields(); self.canvas.fit_view(); self.set_status('Project loaded.')
        except Exception as e:messagebox.showerror('Could not open project',str(e))

if __name__=='__main__': CircleModeller().mainloop()
