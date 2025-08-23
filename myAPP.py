import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from datetime import datetime


class GameDataMigrator:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏数据迁移工具")
        self.root.geometry("850x650")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f8f9fa")

        # 设置中文字体支持和扁平化样式
        self.style = ttk.Style()
        
        # 主色调 - 蓝色系
        primary_color = "#3498db"
        secondary_color = "#2980b9"
        accent_color = "#e74c3c"
        bg_color = "#f0f2f5"
        text_color = "#202124"
        
        # 配置扁平化样式
        # 配置按钮基础样式，增加padding以适应加粗字体
        # 配置按钮基础样式，增加padding并减小字体大小以适应加粗字体
        self.style.configure("TButton", 
                            font= ("SimHei", 9, "normal"),  # 减小字体大小
                            background="#2980b9",
                            foreground="#000000",
                            borderwidth=2,
                            padding=14,  # 增加内边距以适应较长文本
                            # 移除固定宽度限制，让按钮根据文本自动调整宽度
                            relief="raised",
                            bordercolor="#154360")
        self.style.map("TButton", 
                      background=[("active", "#154360"),
                                 ("!disabled", "#2980b9"),
                                 ("disabled", "#95a5a6")],
                      foreground=[("disabled", "#d0d3d4"),
                                 ("!disabled", "#000000"),
                                 ("active", "#000000")],
                      font=[("active", ("SimHei", 9, "normal"))])  # 禁用悬停时的字体加粗效果
        
        self.style.configure("TLabel", 
                            font= ("SimHei", 11),
                            background=bg_color,
                            foreground=text_color)
        
        self.style.configure("Header.TLabel", 
                            font= ("SimHei", 13, "bold"),
                            foreground=primary_color,
                            background=bg_color)
        
        self.style.configure("TNotebook.Tab", 
                            font= ("SimHei", 11),
                            padding=10,
                            background="#e0e0e0",
                            foreground="#808080",  # 未选中状态字体颜色：灰色
                            borderwidth=0,
                            relief="flat")
        self.style.map("TNotebook.Tab", 
                      background=[("selected", "#2980b9"), ("active", "#d0d0d0")],
                      foreground=[("selected", "#000000")])  # 选中状态字体颜色：黑色
        
        # 设置框架样式
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabelframe", 
                            background=bg_color,
                            foreground=text_color,
                            borderwidth=1,
                            relief="flat")
        self.style.configure("TLabelframe.Label", 
                            font= ("SimHei", 10, "bold"),
                            background=bg_color,
                            foreground=primary_color)
        
        # 设置进度条样式
        self.style.configure("Horizontal.TProgressbar", 
                            background=primary_color,
                            borderwidth=0,
                            troughcolor="#e0e0e0",
                            relief="flat")
        
        # 设置树视图样式
        self.style.configure("Treeview", 
                            font= ("SimHei", 11),
                            background=bg_color,
                            foreground=text_color,
                            rowheight=24,
                            fieldbackground=bg_color,
                            borderwidth=1,
                            relief="flat")
        self.style.map("Treeview", 
                      background=[("selected", secondary_color)],
                      foreground=[("selected", "#e6e6e6")])
        
        # 设置组合框样式
        self.style.configure("TCombobox", 
                            font= ("SimHei", 11),
                            background="white",
                            foreground=text_color,
                            borderwidth=1,
                            relief="flat")
        
        # 设置滚动条样式
        self.style.configure("TScrollbar", 
                            background="#e0e0e0",
                            troughcolor=bg_color,
                            borderwidth=0,
                            relief="flat")

        # 数据存储
        self.game_paths = []  # 搜索到的游戏路径
        self.selected_path = tk.StringVar()
        self.game_version = tk.IntVar(value=1)  # 1:正式服, 2:测试服
        self.user_roles = []  # 存储所有角色信息 (路径, 名称, 服务器等)
        self.source_role = tk.StringVar()
        self.target_role = tk.StringVar()
        self.backup_dirs = []  # 存储可用备份目录

        # 创建主界面
        self.create_main_ui()

    def create_main_ui(self):
        """创建主界面"""
        # 创建标签页控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建各个标签页
        self.path_tab = ttk.Frame(self.notebook)
        self.role_tab = ttk.Frame(self.notebook)
        self.migrate_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.path_tab, text="路径选择")
        self.notebook.add(self.role_tab, text="角色选择")
        self.notebook.add(self.migrate_tab, text="数据迁移")

        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # 创建各标签页内容
        self.create_path_tab()
        self.create_role_tab()
        self.create_migrate_tab()

        # 创建状态栏
        self.status_var = tk.StringVar(value="就绪")
        # 使用Text组件替代Label以支持多行显示
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_text = tk.Text(status_frame, height=2, wrap=tk.WORD, state=tk.DISABLED, relief="flat", bg=self.root.cget("bg"))
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # 添加滚动条
        status_scroll = ttk.Scrollbar(status_frame, orient=tk.HORIZONTAL, command=self.status_text.xview)
        status_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_text.configure(xscrollcommand=status_scroll.set)
        
        # 更新状态栏文本的方法
        def update_status(text):
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, text)
            self.status_text.config(state=tk.DISABLED)
            # 自动滚动到末尾
            self.status_text.see(tk.END)
            
        # 替换原有的status_var
        self.status_var.trace_add("write", lambda *args: update_status(self.status_var.get()))
        update_status("就绪")

    def create_path_tab(self):
        """创建路径选择标签页"""
        # 创建标题
        title_label = ttk.Label(self.path_tab, text="游戏路径选择", style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(10, 15))

        # 创建路径搜索框架
        search_frame = ttk.LabelFrame(self.path_tab, text="自动搜索", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        # 搜索按钮
        self.search_btn = ttk.Button(search_frame, text="搜索游戏路径", command=self.search_game_paths)
        self.search_btn.pack(side=tk.LEFT, padx=5)

        # 搜索状态
        self.search_status = ttk.Label(search_frame, text="未搜索", foreground="gray")
        self.search_status.pack(side=tk.LEFT, padx=10)

        # 路径列表框架
        list_frame = ttk.LabelFrame(self.path_tab, text="搜索结果", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 路径列表
        columns = ("index", "path", "size")
        self.path_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        self.path_tree.heading("index", text="序号")
        self.path_tree.heading("path", text="路径")
        self.path_tree.heading("size", text="大小 (MB)")

        self.path_tree.column("index", width=50, anchor=tk.CENTER)
        self.path_tree.column("path", width=400, anchor=tk.W)
        self.path_tree.column("size", width=80, anchor=tk.E)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.path_tree.yview)
        self.path_tree.configure(yscroll=scrollbar.set)

        self.path_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击选择路径
        self.path_tree.bind("<Double-1>", lambda e: self.confirm_path())

        # 版本选择框架
        version_frame = ttk.LabelFrame(self.path_tab, text="游戏版本", padding="10")
        version_frame.pack(fill=tk.X, pady=(0, 10))

        self.version_var = tk.IntVar(value=1)
        ttk.Radiobutton(version_frame, text="正式服 (JX3)", variable=self.version_var, value=1).pack(side=tk.LEFT,
                                                                                                     padx=10)
        ttk.Radiobutton(version_frame, text="测试服 (JX3_EXP)", variable=self.version_var, value=2).pack(side=tk.LEFT,
                                                                                                         padx=10)

        # 确认按钮
        confirm_frame = ttk.Frame(self.path_tab)
        confirm_frame.pack(fill=tk.X, pady=15)

        self.confirm_btn = ttk.Button(confirm_frame, text="确认并继续", command=self.confirm_path, state=tk.DISABLED)
        self.confirm_btn.pack(side=tk.RIGHT, padx=5)

    def create_role_tab(self):
        """创建角色选择标签页"""
        # 创建标题
        title_label = ttk.Label(self.role_tab, text="角色选择", style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(10, 15))

        # 创建角色列表框架
        role_list_frame = ttk.LabelFrame(self.role_tab, text="可用角色", padding="10")
        role_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 角色列表
        columns = ("index", "name", "server", "path")
        self.role_tree = ttk.Treeview(role_list_frame, columns=columns, show="headings", height=8)
        self.role_tree.heading("index", text="序号")
        self.role_tree.heading("name", text="角色名")
        self.role_tree.heading("server", text="服务器")
        self.role_tree.heading("path", text="路径")

        self.role_tree.column("index", width=50, anchor=tk.CENTER)
        self.role_tree.column("name", width=100, anchor=tk.CENTER)
        self.role_tree.column("server", width=150, anchor=tk.CENTER)
        self.role_tree.column("path", width=300, anchor=tk.W)

        # 添加滚动条
        yscroll = ttk.Scrollbar(role_list_frame, orient=tk.VERTICAL, command=self.role_tree.yview)
        xscroll = ttk.Scrollbar(role_list_frame, orient=tk.HORIZONTAL, command=self.role_tree.xview)
        self.role_tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)

        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.role_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 角色选择框架
        selection_frame = ttk.LabelFrame(self.role_tab, text="角色配对", padding="10")
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        # 源角色级联选择
        source_frame = ttk.Frame(selection_frame)
        source_frame.pack(fill=tk.X, pady=5)

        ttk.Label(source_frame, text="源账号:").pack(side=tk.LEFT, padx=5)
        self.source_account_combobox = ttk.Combobox(source_frame, state="readonly")
        self.source_account_combobox.configure(height=5)
        self.source_account_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.source_account_combobox.bind("<<ComboboxSelected>>", self.on_source_account_select)

        # 源角色选择
        source_role_frame = ttk.Frame(selection_frame)
        source_role_frame.pack(fill=tk.X, pady=5)

        ttk.Label(source_role_frame, text="源角色:").pack(side=tk.LEFT, padx=5)
        self.source_combobox = ttk.Combobox(source_role_frame, textvariable=self.source_role, state="readonly")
        self.source_combobox.configure(height=10)
        self.source_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 目标角色级联选择
        target_frame = ttk.Frame(selection_frame)
        target_frame.pack(fill=tk.X, pady=5)

        ttk.Label(target_frame, text="目标账号:").pack(side=tk.LEFT, padx=5)
        self.target_account_combobox = ttk.Combobox(target_frame, state="readonly")
        self.target_account_combobox.configure(height=5)
        self.target_account_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.target_account_combobox.bind("<<ComboboxSelected>>", self.on_target_account_select)

        # 目标角色选择
        target_role_frame = ttk.Frame(selection_frame)
        target_role_frame.pack(fill=tk.X, pady=5)

        ttk.Label(target_role_frame, text="目标角色:").pack(side=tk.LEFT, padx=5)
        self.target_combobox = ttk.Combobox(target_role_frame, textvariable=self.target_role, state="readonly")
        self.target_combobox.configure(height=10)
        self.target_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 操作按钮框架
        btn_frame = ttk.Frame(self.role_tab)
        btn_frame.pack(fill=tk.X, pady=15)

        self.refresh_btn = ttk.Button(btn_frame, text="刷新角色列表", command=self.refresh_roles)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.graph_btn = ttk.Button(btn_frame, text="查看角色图谱", command=self.view_role_graph)
        self.graph_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(btn_frame, text="下一步", command=lambda: self.notebook.select(2), state=tk.DISABLED)
        self.next_btn.pack(side=tk.RIGHT, padx=5)

    def create_migrate_tab(self):
        """创建数据迁移标签页"""
        # 创建标题
        title_label = ttk.Label(self.migrate_tab, text="数据迁移", style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(10, 15))

        # 创建信息框架
        info_frame = ttk.LabelFrame(self.migrate_tab, text="迁移信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # 源角色信息
        source_info_frame = ttk.Frame(info_frame)
        source_info_frame.pack(fill=tk.X, pady=5)

        ttk.Label(source_info_frame, text="源角色路径:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.source_path_var = tk.StringVar()
        ttk.Label(source_info_frame, textvariable=self.source_path_var, foreground="blue").grid(row=0, column=1,
                                                                                                sticky=tk.W, pady=2)

        # 目标角色信息
        target_info_frame = ttk.Frame(info_frame)
        target_info_frame.pack(fill=tk.X, pady=5)

        ttk.Label(target_info_frame, text="目标角色路径:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.target_path_var = tk.StringVar()
        ttk.Label(target_info_frame, textvariable=self.target_path_var, foreground="red").grid(row=0, column=1,
                                                                                               sticky=tk.W, pady=2)

        # 创建日志框架
        log_frame = ttk.LabelFrame(self.migrate_tab, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 日志文本框
        self.log_text = tk.Text(log_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 日志滚动条
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscroll=log_scroll.set)

        # 创建进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.migrate_tab, variable=self.progress_var, length=100,
                                            mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=5, padx=10)

        # 创建按钮框架
        btn_frame = ttk.Frame(self.migrate_tab)
        btn_frame.pack(fill=tk.X, pady=15)

        self.backup_btn = ttk.Button(btn_frame, text="手动备份目标角色", command=self.create_backup, state=tk.DISABLED)
        self.backup_btn.pack(side=tk.LEFT, padx=5)

        self.restore_btn = ttk.Button(btn_frame, text="恢复备份", command=self.restore_backup, state=tk.DISABLED)
        self.restore_btn.pack(side=tk.LEFT, padx=5)

        self.migrate_btn = ttk.Button(btn_frame, text="开始迁移", command=self.start_migration, state=tk.DISABLED)
        self.migrate_btn.pack(side=tk.RIGHT, padx=5)

        self.cancel_btn = ttk.Button(btn_frame, text="取消", command=self.cancel_migration, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

    def on_tab_changed(self, event):
        """标签页切换事件处理"""
        current_tab = self.notebook.select()

        # 如果切换到迁移标签页，更新迁移信息
        if current_tab == str(self.migrate_tab):
            self.update_migrate_info()

    def search_game_paths(self):
        """搜索游戏路径"""
        self.search_btn.config(state=tk.DISABLED)
        self.search_status.config(text="搜索中...", foreground="blue")
        self.status_var.set("正在搜索游戏路径...")
        self.root.update_idletasks()

        # 清空现有结果
        for item in self.path_tree.get_children():
            self.path_tree.delete(item)

        # 在新线程中执行搜索，避免界面冻结
        import threading
        search_thread = threading.Thread(target=self.do_search_game_paths)
        search_thread.daemon = True
        search_thread.start()

    def do_search_game_paths(self):
        """实际执行游戏路径搜索的函数"""
        try:
            # 调用路径搜索函数
            from find_paths import find_target_directories
            self.game_paths = find_target_directories(r'SeasunGame\Game')

            # 在主线程中更新UI
            self.root.after(0, self.update_path_list)

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"搜索失败: {str(e)}"))

    def update_path_list(self):
        """更新路径列表显示"""
        if not self.game_paths:
            self.search_status.config(text="未找到游戏路径", foreground="red")
            self.status_var.set("搜索完成: 未找到游戏路径")
            self.search_btn.config(state=tk.NORMAL)
            return

        # 添加搜索结果到列表
        for i, (path, size, error) in enumerate(self.game_paths, 1):
            size_str = f"{size} MB" if size > 0 else "未知"
            self.path_tree.insert("", tk.END, values=(i, path, size_str))

            # 如果有错误信息，显示在状态栏
            if error:
                self.status_var.set(f"警告: {error}")

        self.search_status.config(text=f"找到 {len(self.game_paths)} 个路径", foreground="green")
        self.status_var.set(f"搜索完成: 找到 {len(self.game_paths)} 个游戏路径")
        self.confirm_btn.config(state=tk.NORMAL)
        self.search_btn.config(state=tk.NORMAL)

    def select_path(self):
        """选择路径"""
        selected = self.path_tree.selection()
        if selected:
            self.confirm_path()

    def confirm_path(self):
        """确认选择的路径"""
        selected = self.path_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择游戏路径")
            return

        # 获取选择的路径
        item = self.path_tree.item(selected[0])
        self.selected_path.set(item["values"][1])

        # 根据选择的版本构建完整游戏路径
        version = self.version_var.get()
        version_dir = "JX3" if version == 1 else "JX3_EXP"
        self.game_path = os.path.join(self.selected_path.get(), version_dir)
        self.userdata_path = os.path.join(self.game_path, r'bin\zhcn_hd\userdata')

        # 验证路径是否存在
        if not os.path.exists(self.userdata_path):
            messagebox.showerror("错误", f"用户数据路径不存在:\n{self.userdata_path}")
            return

        # 加载用户角色
        self.load_user_roles()

        # 切换到角色选择标签页
        self.notebook.select(1)
        self.status_var.set(f"已选择游戏路径: {self.selected_path.get()}")

    def load_user_roles(self):
        """加载用户角色"""
        self.status_var.set("正在加载角色数据...")
        self.root.update_idletasks()

        # 清空现有角色数据
        self.user_roles = []
        for item in self.role_tree.get_children():
            self.role_tree.delete(item)

        # 在新线程中执行角色加载
        import threading
        load_thread = threading.Thread(target=self.do_load_user_roles)
        load_thread.daemon = True
        load_thread.start()

    def do_load_user_roles(self):
        """实际执行角色加载的函数"""
        try:
            # 筛选出有数据的角色
            valid_users = []

            # 检查userdata目录下的用户文件夹
            for user in os.listdir(self.userdata_path):
                user_path = os.path.join(self.userdata_path, user)
                if os.path.isdir(user_path) and len(user) >= 4 and '.dat' not in user:
                    # 检查是否包含大区目录
                    has_region = False
                    for entry in os.listdir(user_path):
                        entry_path = os.path.join(user_path, entry)
                        if os.path.isdir(entry_path) and entry in ['电信区', '双线区', '无界区']:
                            has_region = True
                            break

                    if has_region:
                        valid_users.append(user)

            # 遍历用户_大区_服务器_角色
            count_seq = self.userdata_path.count(os.sep)
            user_roles = []
            self.account_roles = {}

            for user in valid_users:
                user_path = os.path.join(self.userdata_path, user)
                # 初始化账号角色列表
                self.account_roles[user] = []

                # 遍历用户目录下的所有子目录
                for dirpath, _, _ in os.walk(user_path):
                    # 计算当前路径深度
                    current_depth = dirpath.count(os.sep) - count_seq

                    # 角色路径深度为4级 (user/大区/服务器/角色)
                    if current_depth == 4:
                        # 提取角色信息
                        path_parts = dirpath.split(os.sep)
                        role_name = path_parts[-1]
                        server = path_parts[-2]
                        region = path_parts[-3]

                        # 排除名称包含'手动备份'的角色
                        if '手动备份' not in role_name:
                            role_info = {
                                'path': dirpath,
                                'name': role_name,
                                'server': f"{region} - {server}",
                                'index': len(user_roles) + 1
                            }
                            user_roles.append(role_info)
                            # 添加到账号角色映射
                            self.account_roles[user].append(role_info)

            self.user_roles = user_roles
            self.root.after(0, self.update_role_list)

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"加载角色失败: {str(e)}"))

    def update_role_list(self):
        """更新角色列表显示"""
        if not self.user_roles:
            messagebox.showwarning("警告", "未找到任何游戏角色数据")
            self.status_var.set("就绪: 未找到角色数据")
            return

        # 添加角色到列表
        role_names = []
        for role in self.user_roles:
            self.role_tree.insert("", tk.END, values=(
                role['index'],
                role['name'],
                role['server'],
                role['path']
            ))
            role_names.append(f"{role['name']} ({role['server']})")

        # 更新账号下拉框
        account_names = list(self.account_roles.keys())
        self.source_account_combobox['values'] = account_names
        self.target_account_combobox['values'] = account_names

        # 初始化角色下拉框
        if account_names:
            self.source_account_combobox.current(0)
            self.target_account_combobox.current(0 if len(account_names) == 1 else 0)

            # 加载第一个账号的角色
            self.on_source_account_select(None)
            self.on_target_account_select(None)

            self.next_btn.config(state=tk.NORMAL)
            self.backup_btn.config(state=tk.NORMAL)
            self.migrate_btn.config(state=tk.NORMAL)

        self.status_var.set(f"已加载 {len(self.user_roles)} 个角色数据")

    def on_source_account_select(self, event):
        """源账号选择事件处理"""
        selected_account = self.source_account_combobox.get()
        if selected_account in self.account_roles:
            roles = self.account_roles[selected_account]
            role_values = [f"{role['server']} - {role['name']}" for role in roles]
            self.source_combobox['values'] = role_values
            if role_values:
                self.source_combobox.current(0)

    def on_target_account_select(self, event):
        """目标账号选择事件处理"""
        selected_account = self.target_account_combobox.get()
        if selected_account in self.account_roles:
            roles = self.account_roles[selected_account]
            role_values = [f"{role['server']} - {role['name']}" for role in roles]
            self.target_combobox['values'] = role_values
            if role_values:
                self.target_combobox.current(0)

    def refresh_roles(self):
        """刷新角色列表"""
        if hasattr(self, 'userdata_path') and os.path.exists(self.userdata_path):
            self.load_user_roles()
        else:
            messagebox.showinfo("提示", "请先在路径选择标签页选择有效的游戏路径")

    def print_text_tree(self, hierarchy):
        """以纯文本格式打印角色层级结构"""
        result = []
        def traverse(data, level=0, prefix='', is_last=True):
            if level == 0:
                # 账号级别
                for i, (user, regions) in enumerate(data.items()):
                    is_last_user = i == len(data) - 1
                    result.append(f"{user}")
                    traverse(regions, level + 1, '', is_last_user)
            elif level == 1:
                # 大区级别
                for i, (region, servers) in enumerate(data.items()):
                    is_last_region = i == len(data) - 1
                    connector = '└─ ' if is_last_region else '├─ '
                    result.append(f"{prefix}{connector}大区: {region}")
                    new_prefix = prefix + ('    ' if is_last_region else '│   ')
                    traverse(servers, level + 1, new_prefix, is_last_region)
            elif level == 2:
                # 区服级别
                for i, (server, roles) in enumerate(data.items()):
                    is_last_server = i == len(data) - 1
                    connector = '└─ ' if is_last_server else '├─ '
                    result.append(f"{prefix}{connector}区服: {server}")
                    new_prefix = prefix + ('    ' if is_last_server else '│   ')
                    traverse(roles, level + 1, new_prefix, is_last_server)
            elif level == 3:
                # 角色级别
                for i, role in enumerate(data):
                    is_last_role = i == len(data) - 1
                    connector = '└─ ' if is_last_role else '├─ '
                    result.append(f"{prefix}{connector}角色: {role}")

        traverse(hierarchy)
        return '\n'.join(result)

    def show_text_tree(self):
        """显示纯文本树状结构"""
        if not hasattr(self, 'user_roles') or not self.user_roles:
            messagebox.showinfo("提示", "请先在路径选择标签页选择有效的游戏路径并加载角色数据")
            return

        # 构建角色关系数据
        role_hierarchy = {}
        
        # 确保路径结构符合 userdata/账号/大区/区服/角色名
        for role in self.user_roles:
            path_parts = role['path'].split(os.sep)
            
            # 查找 'userdata' 目录的位置
            userdata_index = -1
            for i, part in enumerate(path_parts):
                if part.lower() == 'userdata':
                    userdata_index = i
                    break
            
            if userdata_index == -1:
                # 如果路径中没有 'userdata' 目录，使用原逻辑
                count_seq = self.userdata_path.count(os.sep)
                user = path_parts[count_seq]
                region = path_parts[count_seq + 1]
                server = path_parts[count_seq + 2]
                role_name = path_parts[count_seq + 3]
            else:
                # 按照 userdata/账号/大区/区服/角色名 结构提取
                user = path_parts[userdata_index + 1] if len(path_parts) > userdata_index + 1 else '未知账号'
                region = path_parts[userdata_index + 2] if len(path_parts) > userdata_index + 2 else '未知大区'
                server = path_parts[userdata_index + 3] if len(path_parts) > userdata_index + 3 else '未知区服'
                role_name = path_parts[userdata_index + 4] if len(path_parts) > userdata_index + 4 else '未知角色'

            # 构建层级结构
            if user not in role_hierarchy:
                role_hierarchy[user] = {}
            if region not in role_hierarchy[user]:
                role_hierarchy[user][region] = {}
            if server not in role_hierarchy[user][region]:
                role_hierarchy[user][region][server] = []
            role_hierarchy[user][region][server].append(role_name)

        # 生成纯文本树
        text_tree = self.print_text_tree(role_hierarchy)

        # 显示在新窗口
        tree_window = tk.Toplevel(self.root)
        tree_window.title("角色层级结构")
        tree_window.geometry("600x400")
        tree_window.resizable(True, True)

        # 添加滚动条
        yscroll = ttk.Scrollbar(tree_window)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(tree_window, yscrollcommand=yscroll.set, wrap=tk.NONE)
        text_widget.pack(fill=tk.BOTH, expand=True)
        yscroll.config(command=text_widget.yview)

        # 添加文本
        text_widget.insert(tk.END, text_tree)

        # 添加复制按钮
        def copy_to_clipboard():
            tree_window.clipboard_clear()
            tree_window.clipboard_append(text_tree)
            messagebox.showinfo("提示", "已复制到剪贴板")

        copy_btn = ttk.Button(tree_window, text="复制到剪贴板", command=copy_to_clipboard)
        copy_btn.pack(pady=5)

    def view_role_graph(self):
        """查看角色图谱 - 仅显示纯文本层级结构"""
        # 直接调用纯文本展示功能
        self.show_text_tree()

    # 保留draw_tree方法但标记为废弃
    def draw_tree(self, canvas, hierarchy, x=200, y=50, level=0, width_per_level=200, height_per_level=60):
        """[已废弃] 绘制树形图"""
        pass

    # 保留图形相关事件处理方法但标记为废弃
    def on_graph_press(self, event):
        """[已废弃] 处理鼠标按下事件"""
        pass

    def on_graph_drag(self, event):
        """[已废弃] 处理鼠标拖动事件"""
        pass

    def on_graph_release(self, event):
        """[已废弃] 处理鼠标释放事件"""
        pass

    def on_graph_zoom(self, event):
        """[已废弃] 处理鼠标滚轮缩放事件"""
        pass

    def on_graph_zoom_linux(self, event):
        """[已废弃] 处理Linux鼠标缩放事件"""
        pass

    def draw_tree(self, canvas, hierarchy, x=200, y=50, level=0, width_per_level=200, height_per_level=60):
        """在画布上绘制树形图 - 简化的层级结构: 账号→大区→区服→角色名"""
        if not hierarchy:
            return y

        # 计算当前层级的项数
        items = list(hierarchy.items())
        total_items = len(items)

        # 计算起始Y坐标
        start_y = y - (total_items * height_per_level) / 2

        for i, (name, children) in enumerate(items):
            # 计算当前项的坐标
            current_x = x + level * width_per_level
            current_y = start_y + i * height_per_level

            # 根据层级设置节点样式和标签
            node_radius = 25
            if level == 0:  # 账号节点
                canvas.create_oval(current_x - node_radius, current_y - node_radius,
                                  current_x + node_radius, current_y + node_radius,
                                  fill="lightcoral")
                canvas.create_text(current_x, current_y, text=f"账号: {name}", font=('SimHei', 10, 'bold'))
            elif level == 1:  # 大区节点
                canvas.create_oval(current_x - node_radius, current_y - node_radius,
                                  current_x + node_radius, current_y + node_radius,
                                  fill="lightblue")
                canvas.create_text(current_x, current_y, text=f"大区: {name}", font=('SimHei', 10))
            elif level == 2:  # 区服节点
                canvas.create_oval(current_x - node_radius, current_y - node_radius,
                                  current_x + node_radius, current_y + node_radius,
                                  fill="lightgreen")
                canvas.create_text(current_x, current_y, text=f"区服: {name}", font=('SimHei', 10))

            # 如果有子节点，递归绘制
            if children and isinstance(children, dict):
                next_y = self.draw_tree(canvas, children, x, current_y, level + 1,
                                      width_per_level, height_per_level)
                # 绘制连接线到下一级节点
                child_x = x + (level + 1) * width_per_level
                child_y = current_y
                canvas.create_line(current_x + node_radius, current_y,
                                  child_x - node_radius, child_y)
            elif children and isinstance(children, list):
                # 绘制角色节点
                role_height_per_level = height_per_level + 10
                role_start_y = current_y - (len(children) * role_height_per_level) / 2
                for j, role_name in enumerate(children):
                    role_x = x + (level + 1) * width_per_level
                    role_y = role_start_y + j * role_height_per_level
                    canvas.create_rectangle(role_x - 100, role_y - 15,
                                           role_x + 100, role_y + 15,
                                           fill="lightyellow")
                    canvas.create_text(role_x, role_y, text=f"角色: {role_name}", font=('SimHei', 10), width=190)
                    # 绘制区服到角色的连接线
                    canvas.create_line(current_x + node_radius, current_y,
                                      role_x - 100, role_y)

        return start_y + total_items * height_per_level

    def on_graph_press(self, event):
        """鼠标按下事件处理"""
        canvas = event.widget
        canvas.last_x = event.x
        canvas.last_y = event.y
        canvas.panning = True
        canvas.config(cursor="fleur")

    def on_graph_drag(self, event):
        """鼠标拖动事件处理"""
        canvas = event.widget
        if canvas.panning:
            # 计算位移
            dx = event.x - canvas.last_x
            dy = event.y - canvas.last_y
            canvas.last_x = event.x
            canvas.last_y = event.y
            # 移动视图
            canvas.xview_scroll(-dx // 1, "units")
            canvas.yview_scroll(-dy // 1, "units")

    def on_graph_release(self, event):
        """鼠标释放事件处理"""
        canvas = event.widget
        canvas.panning = False
        canvas.config(cursor="arrow")

    def on_graph_zoom(self, event):
        """鼠标滚轮缩放事件处理(Windows)"""
        canvas = event.widget
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_canvas(canvas, scale_factor, event.x, event.y)

    def on_graph_zoom_linux(self, event):
        """鼠标滚轮缩放事件处理(Linux)"""
        canvas = event.widget
        if event.num == 4:  # 滚轮向上
            scale_factor = 1.1
        elif event.num == 5:  # 滚轮向下
            scale_factor = 0.9
        else:
            return
        self.zoom_canvas(canvas, scale_factor, event.x, event.y)

    def zoom_canvas(self, canvas, scale_factor, x, y):
        """缩放画布"""
        # 记录当前缩放因子
        canvas.scale_factor *= scale_factor
        # 限制缩放范围
        if canvas.scale_factor < 0.5:
            canvas.scale_factor = 0.5
        elif canvas.scale_factor > 3.0:
            canvas.scale_factor = 3.0

        # 计算缩放后的视口
        region = canvas.bbox("all")
        if region:
            # 计算新的视口中心
            center_x = x
            center_y = y

            # 调整画布的滚动区域
            canvas.configure(scrollregion=region)
            # 移动到缩放中心
            canvas.xview_moveto((center_x / canvas.winfo_width()) * (1 - scale_factor) + canvas.xview()[0])
            canvas.yview_moveto((center_y / canvas.winfo_height()) * (1 - scale_factor) + canvas.yview()[0])

        self.status_var.set(f"已加载 {len(self.user_roles)} 个角色数据")



    def update_migrate_info(self):
        """更新迁移信息"""
        # 获取选中的源账号和角色
        source_account = self.source_account_combobox.get()
        source_role_text = self.source_combobox.get()

        # 获取选中的目标账号和角色
        target_account = self.target_account_combobox.get()
        target_role_text = self.target_combobox.get()

        # 查找源角色信息
        if source_account in self.account_roles and source_role_text:
            for role in self.account_roles[source_account]:
                if f"{role['server']} - {role['name']}" == source_role_text:
                    self.source_path_var.set(role['path'])
                    break

        # 查找目标角色信息
        if target_account in self.account_roles and target_role_text:
            for role in self.account_roles[target_account]:
                if f"{role['server']} - {role['name']}" == target_role_text:
                    self.target_path_var.set(role['path'])
                    break

        # 启用/禁用按钮
        source_valid = source_account in self.account_roles and source_role_text
        target_valid = target_account in self.account_roles and target_role_text
        different_roles = source_role_text != target_role_text or source_account != target_account

        if source_valid and target_valid and different_roles:
            self.migrate_btn.config(state=tk.NORMAL)
            self.backup_btn.config(state=tk.NORMAL)
            self.restore_btn.config(state=tk.NORMAL)
        else:
            self.migrate_btn.config(state=tk.DISABLED)

    def create_backup(self):
        """创建目标角色备份"""
        target_idx = self.target_combobox.current()
        if target_idx < 0 or target_idx >= len(self.user_roles):
            messagebox.showwarning("警告", "请先选择有效的目标角色")
            return

        target_role = self.user_roles[target_idx]
        target_path = target_role['path']

        # 生成备份路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{target_role['name']}_手动备份_{timestamp}"
        backup_path = os.path.join(os.path.dirname(target_path), backup_dir)

        try:
            # 创建备份
            self.log_message(f"开始创建手动备份: {backup_path}")
            self.status_var.set("正在创建手动备份...")
            self.backup_btn.config(state=tk.DISABLED)

            # 使用线程执行备份，避免界面冻结
            import threading
            backup_thread = threading.Thread(
                target=self.do_create_backup,
                args=(target_path, backup_path)
            )
            backup_thread.daemon = True
            backup_thread.start()

        except Exception as e:
            self.show_error(f"创建备份失败: {str(e)}")
            self.backup_btn.config(state=tk.NORMAL)

    def do_create_backup(self, source, dest):
        """实际执行备份操作"""
        try:
            # 确保目标目录不存在
            if os.path.exists(dest):
                shutil.rmtree(dest)

            # 复制目录
            shutil.copytree(source, dest)

            # 记录备份路径
            self.backup_dirs.append(dest)

            self.root.after(0, lambda: self.log_message(f"手动备份创建成功: {dest}"))
            self.root.after(0, lambda: messagebox.showinfo("成功", f"手动备份创建成功:\n{dest}"))
            self.root.after(0, lambda: self.status_var.set("手动备份创建成功"))
            self.root.after(0, lambda: self.backup_btn.config(state=tk.NORMAL))

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"备份失败: {str(e)}"))
            self.root.after(0, lambda: self.backup_btn.config(state=tk.NORMAL))

    def restore_backup(self):
        """恢复备份"""
        # 查找所有备份
        target_idx = self.target_combobox.current()
        if target_idx < 0 or target_idx >= len(self.user_roles):
            messagebox.showwarning("警告", "请先选择有效的目标角色")
            return

        target_role = self.user_roles[target_idx]
        target_path = target_role['path']
        backup_parent = os.path.dirname(target_path)

        # 查找所有备份目录
        backups = []
        for entry in os.listdir(backup_parent):
            entry_path = os.path.join(backup_parent, entry)
            if os.path.isdir(entry_path) and (entry.startswith(f"{target_role['name']}_手动备份_") or entry.startswith(
                    f"{target_role['name']}_备份_")):
                # 提取时间戳
                try:
                    if "_手动备份_" in entry:
                        timestamp_str = entry.split("_手动备份_")[1]
                    else:
                        timestamp_str = entry.split("_备份_")[1]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    backups.append((timestamp, entry, entry_path))
                except:
                    continue

        # 按时间戳排序，最新的在前
        backups.sort(reverse=True, key=lambda x: x[0])

        if not backups:
            messagebox.showinfo("提示", "未找到任何备份文件")
            return

        # 创建备份选择对话框
        backup_window = tk.Toplevel(self.root)
        backup_window.title("选择备份文件")
        backup_window.geometry("500x300")
        backup_window.resizable(True, True)
        backup_window.transient(self.root)
        backup_window.grab_set()

        # 创建列表框
        listbox = tk.Listbox(backup_window, selectmode=tk.SINGLE, font=("SimHei", 10), fg="#e6e6e6", bg="#2c3e50")
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加备份到列表
        backup_paths = []
        for timestamp, name, path in backups:
            display_name = f"{name} ({timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
            listbox.insert(tk.END, display_name)
            backup_paths.append(path)

        # 滚动条
        scrollbar = ttk.Scrollbar(listbox, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮框架
        btn_frame = ttk.Frame(backup_window)
        btn_frame.pack(fill=tk.X, pady=10)

        def do_restore():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择一个备份文件")
                return

            selected_path = backup_paths[selection[0]]

            # 确认恢复
            confirm = messagebox.askyesno(
                "确认恢复",
                f"确定要将备份恢复到目标角色吗?\n\n备份: {selected_path}\n目标: {target_path}\n\n此操作将覆盖现有数据!"
            )

            if confirm:
                backup_window.destroy()
                self.status_var.set("正在恢复备份...")
                self.restore_btn.config(state=tk.DISABLED)

                # 在新线程中执行恢复
                import threading
                restore_thread = threading.Thread(
                    target=self.do_restore_backup,
                    args=(selected_path, target_path)
                )
                restore_thread.daemon = True
                restore_thread.start()

        ttk.Button(btn_frame, text="恢复", command=do_restore).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=backup_window.destroy).pack(side=tk.RIGHT, padx=5)

        # 默认选择最新备份
        if backups:
            listbox.selection_set(0)

    def do_restore_backup(self, source, dest):
        """实际执行恢复操作"""
        try:
            # 清空目标目录
            if os.path.exists(dest):
                for item in os.listdir(dest):
                    item_path = os.path.join(dest, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    else:
                        shutil.rmtree(item_path)

            # 恢复备份
            for item in os.listdir(source):
                src_item = os.path.join(source, item)
                dest_item = os.path.join(dest, item)

                if os.path.isdir(src_item):
                    shutil.copytree(src_item, dest_item)
                else:
                    shutil.copy2(src_item, dest_item)

            self.root.after(0, lambda: self.log_message(f"备份恢复成功: {source}"))
            self.root.after(0, lambda: messagebox.showinfo("成功", "备份恢复成功"))
            self.root.after(0, lambda: self.status_var.set("备份恢复成功"))
            self.root.after(0, lambda: self.restore_btn.config(state=tk.NORMAL))

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"恢复失败: {str(e)}"))
            self.root.after(0, lambda: self.restore_btn.config(state=tk.NORMAL))

    def start_migration(self):
        """开始数据迁移 - 不创建迁移前备份"""
        # 检查源角色和目标角色是否选择
        source_account = self.source_account_combobox.get()
        source_role_text = self.source_combobox.get()
        target_account = self.target_account_combobox.get()
        target_role_text = self.target_combobox.get()

        if not source_role_text or not target_role_text:
            messagebox.showwarning("警告", "请选择源角色和目标角色")
            return

        if source_role_text == target_role_text and source_account == target_account:
            messagebox.showwarning("警告", "源角色和目标角色不能相同")
            return

        # 查找源角色信息
        source_role = None
        if source_account in self.account_roles:
            for role in self.account_roles[source_account]:
                if f"{role['server']} - {role['name']}" == source_role_text:
                    source_role = role
                    break

        # 查找目标角色信息
        target_role = None
        if target_account in self.account_roles:
            for role in self.account_roles[target_account]:
                if f"{role['server']} - {role['name']}" == target_role_text:
                    target_role = role
                    break

        if not source_role or not target_role:
            messagebox.showerror("错误", "无法找到选定的角色信息")
            return

        source_path = source_role['path']
        target_path = target_role['path']

        # 直接执行迁移，不创建迁移前备份
        self.log_message(f"开始数据迁移，不创建迁移前备份...")
        self.log_message(f"源角色: {source_path}")
        self.log_message(f"目标角色: {target_path}")

        self.migrate_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.status_var.set("正在执行数据迁移...")

        # 在新线程中执行迁移
        import threading
        migrate_thread = threading.Thread(
            target=self.do_migration,
            args=(source_path, target_path)
        )
        migrate_thread.daemon = True
        migrate_thread.start()

    def do_migration(self, source_path, target_path):
        """执行数据迁移（直接复制整个源角色目录到目标角色目录，不计算相同文件）"""
        try:
            # 计算源目录中的文件总数，用于进度显示
            total_files = 0
            for root, _, files in os.walk(source_path):
                total_files += len(files)

            if total_files == 0:
                self.root.after(0, lambda: messagebox.showinfo("提示", "源角色目录为空，无需迁移"))
                self.root.after(0, lambda: self.finish_migration(True))
                return

            # 如果目标目录存在，先删除
            if os.path.exists(target_path):
                shutil.rmtree(target_path)

            # 创建目标目录
            os.makedirs(target_path, exist_ok=True)

            # 复制文件并更新进度
            copied_files = 0
            for root, dirs, files in os.walk(source_path):
                # 创建目标目录结构
                rel_path = os.path.relpath(root, source_path)
                target_root = os.path.join(target_path, rel_path)
                os.makedirs(target_root, exist_ok=True)

                # 复制文件
                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(target_root, file)

                    shutil.copy2(src_file, dest_file)

                    copied_files += 1

                    # 更新进度
                    progress = (copied_files / total_files) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))

                    # 更新日志
                    if copied_files % 10 == 0 or copied_files == total_files:
                        self.root.after(0, lambda f=copied_files, t=total_files: 
                                        self.log_message(f"已复制 {f}/{t} 文件"))

            self.root.after(0, lambda: self.log_message(f"数据迁移完成! 共复制 {copied_files} 个文件"))
            self.root.after(0, lambda: self.finish_migration(True))

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"迁移失败: {str(e)}"))
            self.root.after(0, lambda: self.finish_migration(False))

    def clean_empty_directories(self, root_dir):
        """递归清理空目录"""
        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
            if not dirnames and not filenames:
                try:
                    os.rmdir(dirpath)
                    self.root.after(0, lambda p=dirpath: self.log_message(f"已删除空目录: {p}"))
                except OSError:
                    pass

    def finish_migration(self, success):
        """完成迁移"""
        if success:
            self.status_var.set("迁移完成成功")
            self.progress_var.set(100)
            messagebox.showinfo("成功", "数据迁移已完成!")
        else:
            self.status_var.set("迁移失败")
            self.progress_var.set(0)

        self.migrate_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def cancel_migration(self):
        """取消迁移"""
        if messagebox.askyesno("确认取消", "确定要取消当前迁移操作吗?"):
            self.status_var.set("迁移已取消")
            self.progress_var.set(0)
            self.log_message("迁移操作已取消")
            self.migrate_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)

    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def show_error(self, message):
        """显示错误消息"""
        messagebox.showerror("错误", message)
        self.log_message(f"错误: {message}")
        self.status_var.set(f"错误: {message[:50]}")

    def refresh_roles(self):
        """刷新角色列表"""
        if hasattr(self, 'userdata_path') and os.path.exists(self.userdata_path):
            self.load_user_roles()
        else:
            messagebox.showinfo("提示", "请先在路径选择标签页选择有效的游戏路径")


if __name__ == "__main__":
    root = tk.Tk()

    # 设置窗口背景
    root.configure(bg="#f8f9fa")

    # 设置中文字体
    font_config = ("SimHei", 10)
    root.option_add("*Font", font_config)

    app = GameDataMigrator(root)
    root.mainloop()