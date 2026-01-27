import customtkinter as ctk
import math

class PerspectiveGrid(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg="#0B0F19", highlightthickness=0, **kwargs)
        self.width = 1000
        self.height = 800
        
        # 消失点 (初始在中心)
        self.vp_x = self.width / 2
        self.vp_y = self.height / 3 # 地平线偏上一点，更有纵深感
        
        # 绑定鼠标移动
        self.bind("<Motion>", self.on_mouse_move)
        
        # 启动动画循环
        self.after(10, self.draw_loop)

    def on_mouse_move(self, event):
        # 让消失点反向移动，模拟镜头转动
        # 阻尼系数 10，让移动不那么剧烈
        target_x = self.winfo_width()/2 + (self.winfo_width()/2 - event.x) / 10
        target_y = self.winfo_height()/3 + (self.winfo_height()/2 - event.y) / 20
        
        # 简单的平滑插值
        self.vp_x += (target_x - self.vp_x) * 0.1
        self.vp_y += (target_y - self.vp_y) * 0.1

    def draw_loop(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        
        # 1. 画放射线 (纵向网格)
        # 即使线是直的，汇聚到一个点就会产生 3D 感
        for i in range(-5, 16): 
            # 底部通过点
            base_x = w/2 + (i - 5) * 200 
            # 颜色：带点透明感的青色
            self.create_line(self.vp_x, self.vp_y, base_x, h, fill="#1e293b", width=2)

        # 2. 画横线 (横向网格)
        # 间距是指数的，越远越密
        for i in range(1, 20):
            offset = i * i * 3  # 指数增长的间距
            line_y = self.vp_y + offset
            if line_y > h: break
            self.create_line(0, line_y, w, line_y, fill="#0f172a", width=1)
            
        # 3. 画地平线光晕
        self.create_line(0, self.vp_y, w, self.vp_y, fill="#38bdf8", width=2)
        
        self.after(30, self.draw_loop)

if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("1000x800")
    grid = PerspectiveGrid(app)
    grid.pack(fill="both", expand=True)
    
    # 放一个浮动按钮看看效果
    btn = ctk.CTkButton(app, text="SYSTEM STATUS", width=200)
    btn.place(relx=0.5, rely=0.5, anchor="center")
    
    app.mainloop()