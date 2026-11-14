import tkinter as tk
from math import cos, sin, pi
from geometry.primitives import Point

class ModelingCanvas(tk.Canvas):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, bg='#101827', highlightthickness=0, **kwargs)
        self.app=app; self.scale=1.0; self.offset=Point(0,0)
        self.drag_mode=None; self.last_mouse=None; self.preview_center=None; self.preview_radius=0
        self.bind('<Button-1>',self.on_left); self.bind('<B1-Motion>',self.on_drag); self.bind('<ButtonRelease-1>',self.on_release)
        self.bind('<Motion>',self.on_motion); self.bind('<MouseWheel>',self.on_wheel)
        self.bind('<Button-4>',lambda e:self.zoom(e,1.12)); self.bind('<Button-5>',lambda e:self.zoom(e,1/1.12))
        self.bind('<Button-2>',self.pan_start); self.bind('<B2-Motion>',self.pan_move)
        self.bind('<Button-3>',self.pan_start); self.bind('<B3-Motion>',self.pan_move)
        self.bind('<Configure>',lambda e:self.redraw())
    def to_screen(self,p): return (p.x*self.scale+self.offset.x, p.y*self.scale+self.offset.y)
    def to_world(self,x,y): return Point((x-self.offset.x)/self.scale,(y-self.offset.y)/self.scale)
    def zoom(self,event,factor):
        before=self.to_world(event.x,event.y); self.scale=max(.15,min(5,self.scale*factor))
        self.offset=Point(event.x-before.x*self.scale,event.y-before.y*self.scale); self.redraw()
    def on_wheel(self,e): self.zoom(e,1.12 if e.delta>0 else 1/1.12)
    def pan_start(self,e): self.drag_mode='pan'; self.last_mouse=Point(e.x,e.y)
    def pan_move(self,e):
        if self.drag_mode!='pan': return
        self.offset += Point(e.x-self.last_mouse.x,e.y-self.last_mouse.y); self.last_mouse=Point(e.x,e.y); self.redraw()
    def on_left(self,e):
        w=self.to_world(e.x,e.y)
        if self.app.tool.get()=='Add Circle':
            if self.preview_center is None:
                self.preview_center=w; self.app.set_status('Move the mouse to preview the radius, then click to confirm.')
            else:
                r=(w-self.preview_center).length()
                if r<2: self.app.set_status('Radius is too small. Click farther from the centre.'); return
                self.app.add_circle(self.preview_center,r); self.preview_center=None; self.redraw()
            return
        hit=self.hit_circle(w)
        if hit:
            self.app.select_circle(hit.id)
            edge=abs((w-hit.center).length()-hit.radius)
            self.drag_mode='resize' if edge<max(9/self.scale,hit.radius*.12) else 'move'
            self.last_mouse=w
        else:
            self.app.select_circle(None); self.drag_mode=None
        self.redraw()
    def hit_circle(self,p):
        for c in reversed(self.app.circles):
            if (p-c.center).length() <= c.radius: return c
        return None
    def on_drag(self,e):
        if not self.drag_mode or self.drag_mode=='pan': return
        w=self.to_world(e.x,e.y); c=self.app.selected_circle()
        if not c: return
        if self.drag_mode=='move': c.center=w
        elif self.drag_mode=='resize': c.radius=max(2,(w-c.center).length())
        self.app.shape=None; self.app.update_circle_fields(); self.redraw()
    def on_release(self,e):
        if self.drag_mode in ('move','resize'): self.app.push_history()
        self.drag_mode=None
    def on_motion(self,e):
        if self.preview_center is not None:
            self.preview_radius=(self.to_world(e.x,e.y)-self.preview_center).length(); self.redraw()
    def fit_view(self):
        if not self.app.circles: self.scale=1; self.offset=Point(80,80); self.redraw(); return
        minx=min(c.center.x-c.radius for c in self.app.circles); maxx=max(c.center.x+c.radius for c in self.app.circles)
        miny=min(c.center.y-c.radius for c in self.app.circles); maxy=max(c.center.y+c.radius for c in self.app.circles)
        w=max(1,self.winfo_width()-100); h=max(1,self.winfo_height()-100)
        self.scale=min(w/max(maxx-minx,1),h/max(maxy-miny,1),3)
        self.offset=Point((self.winfo_width()-(minx+maxx)*self.scale)/2,(self.winfo_height()-(miny+maxy)*self.scale)/2); self.redraw()
    def draw_polyline(self,pts,color,width=2,dash=None):
        if len(pts)<2:return
        coords=[]
        for p in pts: coords.extend(self.to_screen(p))
        self.create_line(*coords,fill=color,width=width,dash=dash,smooth=False)
    def redraw(self):
        self.delete('all'); w=max(self.winfo_width(),1); h=max(self.winfo_height(),1)
        step=50*self.scale
        if step>=12:
            ox=self.offset.x%step; oy=self.offset.y%step
            for x in range(int(ox),w,int(step)): self.create_line(x,0,x,h,fill='#1c2a3d')
            for y in range(int(oy),h,int(step)): self.create_line(0,y,w,y,fill='#1c2a3d')
        # generated filled region
        s=self.app.shape
        if s and s.upper and s.lower:
            poly=s.upper+s.lower[::-1]; coords=[]
            for p in poly: coords.extend(self.to_screen(p))
            self.create_polygon(*coords,fill='#174e57',outline='#48d6c7',width=2)
            if self.app.show_centerline.get(): self.draw_polyline(s.centerline,'#f4c76b',2,(5,3))
            if self.app.show_contacts.get():
                for p in s.contact_points:
                    x,y=self.to_screen(p); self.create_oval(x-4,y-4,x+4,y+4,fill='#ffbd69',outline='')
            if self.app.show_tangents.get():
                for p,v in s.tangent_vectors:
                    a=self.to_screen(p); b=self.to_screen(p+v*.18); self.create_line(*a,*b,fill='#f59e0b',arrow=tk.LAST,width=2)
        for c in self.app.circles:
            x,y=self.to_screen(c.center); rr=c.radius*self.scale
            selected=c.id==self.app.selected_id
            self.create_oval(x-rr,y-rr,x+rr,y+rr,outline='#ffd166' if selected else '#7ca6c9',width=2 if selected else 1.5)
            self.create_oval(x-3,y-3,x+3,y+3,fill='#f8fafc',outline='')
            self.create_text(x,y-rr-13,text=f'{c.id}  r={c.radius:.1f}',fill='#cbd5e1',font=('Segoe UI',9))
            if selected: self.create_oval(x-rr-4,y-rr-4,x+rr+4,y+rr+4,outline='#ffd166',dash=(3,3))
        if self.preview_center is not None:
            x,y=self.to_screen(self.preview_center); rr=self.preview_radius*self.scale
            self.create_oval(x-rr,y-rr,x+rr,y+rr,outline='#4ade80',dash=(4,3),width=2)
            self.create_oval(x-3,y-3,x+3,y+3,fill='#4ade80',outline='')
        self.create_text(12,h-12,anchor='sw',text=f'Zoom {self.scale:.2f}x  |  Middle/right-drag to pan  |  Wheel to zoom',fill='#64748b',font=('Segoe UI',8))
