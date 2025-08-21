import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from datetime import datetime


class GameDataMigrator:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏数据迁移工具")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TNotebook.Tab", font=("SimHei", 10))
        self.style.configure("Header.TLabel", font=("SimHei", 12, "bold"))

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
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_path_tab(self):
        """创建路径选择标签页"""
        # 创建标题
        title_label = ttk.Label(self.path_tab, text="游戏路径选择", style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # 创建路径搜索框架
        search_frame = ttk.LabelFrame(self.path_tab, text="自动搜索", padding="10")
        search_frame.pack(fill=tk.X, pady=5)

        # 搜索按钮
        self.search_btn = ttk.Button(search_frame, text="搜索游戏路径", command=self.search_game_paths)
        self.search_btn.pack(side=tk.LEFT, padx=5)

        # 搜索状态
        self.search_status = ttk.Label(search_frame, text="未搜索", foreground="gray")
        self.search_status.pack(side=tk.LEFT, padx=10)

        # 路径列表框架
        list_frame = ttk.LabelFrame(self.path_tab, text="搜索结果", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

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
        version_frame.pack(fill=tk.X, pady=5)

        self.version_var = tk.IntVar(value=1)
        ttk.Radiobutton(version_frame, text="正式服 (JX3)", variable=self.version_var, value=1).pack(side=tk.LEFT,
                                                                                                     padx=10)
        ttk.Radiobutton(version_frame, text="测试服 (JX3_EXP)", variable=self.version_var, value=2).pack(side=tk.LEFT,
                                                                                                         padx=10)

        # 确认按钮
        confirm_frame = ttk.Frame(self.path_tab)
        confirm_frame.pack(fill=tk.X, pady=10)

        self.confirm_btn = ttk.Button(confirm_frame, text="确认并继续", command=self.confirm_path, state=tk.DISABLED)
        self.confirm_btn.pack(side=tk.RIGHT, padx=5)

    def create_role_tab(self):
        """创建角色选择标签页"""
        # 创建标题
        title_label = ttk.Label(self.role_tab, text="角色选择", style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # 创建角色列表框架
        role_list_frame = ttk.LabelFrame(self.role_tab, text="可用角色", padding="10")
        role_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

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
        selection_frame.pack(fill=tk.X, pady=5)

        # 源角色选择
        source_frame = ttk.Frame(selection_frame)
        source_frame.pack(fill=tk.X, pady=5)

        ttk.Label(source_frame, text="源角色:").pack(side=tk.LEFT, padx=5)
        self.source_combobox = ttk.Combobox(source_frame, textvariable=self.source_role, state="readonly", width=30)
        self.source_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 目标角色选择
        target_frame = ttk.Frame(selection_frame)
        target_frame.pack(fill=tk.X, pady=5)

        ttk.Label(target_frame, text="目标角色:").pack(side=tk.LEFT, padx=5)
        self.target_combobox = ttk.Combobox(target_frame, textvariable=self.target_role, state="readonly", width=30)
        self.target_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 操作按钮框架
        btn_frame = ttk.Frame(self.role_tab)
        btn_frame.pack(fill=tk.X, pady=10)

        self.refresh_btn = ttk.Button(btn_frame, text="刷新角色列表", command=self.refresh_roles)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(btn_frame, text="下一步", command=lambda: self.notebook.select(2), state=tk.DISABLED)
        self.next_btn.pack(side=tk.RIGHT, padx=5)

    def create_migrate_tab(self):
        """创建数据迁移标签页"""
        # 创建标题
        title_label = ttk.Label(self.migrate_tab, text="数据迁移", style="Header.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # 创建信息框架
        info_frame = ttk.LabelFrame(self.migrate_tab, text="迁移信息", padding="10")
        info_frame.pack(fill=tk.X, pady=5)

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
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

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
        btn_frame.pack(fill=tk.X, pady=10)

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

            for user in valid_users:
                user_path = os.path.join(self.userdata_path, user)

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

                        user_roles.append({
                            'path': dirpath,
                            'name': role_name,
                            'server': f"{region} - {server}",
                            'index': len(user_roles) + 1
                        })

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

        # 更新下拉框
        self.source_combobox['values'] = role_names
        self.target_combobox['values'] = role_names

        if role_names:
            self.source_combobox.current(0)
            # 如果有多个角色，默认选择第二个作为目标
            target_index = 1 if len(role_names) > 1 else 0
            self.target_combobox.current(target_index)
            self.next_btn.config(state=tk.NORMAL)
            self.backup_btn.config(state=tk.NORMAL)
            self.migrate_btn.config(state=tk.NORMAL)

        self.status_var.set(f"已加载 {len(self.user_roles)} 个角色数据")

    def refresh_roles(self):
        """刷新角色列表"""
        if hasattr(self, 'userdata_path') and os.path.exists(self.userdata_path):
            self.load_user_roles()
        else:
            messagebox.showinfo("提示", "请先在路径选择标签页选择有效的游戏路径")

    def update_migrate_info(self):
        """更新迁移信息"""
        # 获取选中的源角色和目标角色
        source_idx = self.source_combobox.current()
        target_idx = self.target_combobox.current()

        if 0 <= source_idx < len(self.user_roles):
            source_role = self.user_roles[source_idx]
            self.source_path_var.set(source_role['path'])

        if 0 <= target_idx < len(self.user_roles):
            target_role = self.user_roles[target_idx]
            self.target_path_var.set(target_role['path'])

        # 启用/禁用按钮
        if source_idx != target_idx and source_idx >= 0 and target_idx >= 0:
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
        listbox = tk.Listbox(backup_window, selectmode=tk.SINGLE, font=("SimHei", 10))
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
        source_idx = self.source_combobox.current()
        target_idx = self.target_combobox.current()

        if source_idx == -1 or target_idx == -1:
            messagebox.showwarning("警告", "请选择源角色和目标角色")
            return

        if source_idx == target_idx:
            messagebox.showwarning("警告", "源角色和目标角色不能相同")
            return

        # 获取源角色和目标角色路径
        source_role = self.user_roles[source_idx]
        target_role = self.user_roles[target_idx]

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
        """执行数据迁移"""
        try:
            # 获取源目录下的所有文件和子目录
            all_files = []
            for root, _, files in os.walk(source_path):
                for file in files:
                    all_files.append(os.path.join(root, file))

            total_files = len(all_files)
            if total_files == 0:
                self.root.after(0, lambda: messagebox.showwarning("警告", "源角色目录中没有找到任何文件"))
                self.root.after(0, lambda: self.finish_migration(False))
                return

            # 执行文件复制
            copied_files = 0

            for i, src_file in enumerate(all_files, 1):
                # 计算相对路径
                rel_path = os.path.relpath(src_file, source_path)
                dest_file = os.path.join(target_path, rel_path)

                # 创建目标目录
                dest_dir = os.path.dirname(dest_file)
                os.makedirs(dest_dir, exist_ok=True)

                # 复制文件
                shutil.copy2(src_file, dest_file)

                copied_files += 1

                # 更新进度
                progress = (copied_files / total_files) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))

                # 更新日志（每10个文件更新一次，避免UI频繁刷新）
                if i % 1 == 0 or i == total_files:
                    self.root.after(0, lambda f=copied_files, t=total_files:
                    self.log_message(f"已复制 {f}/{t} 文件 ({int(f / t * 100)}%)"))

            self.root.after(0, lambda: self.log_message(f"数据迁移完成! 共复制 {copied_files} 个文件"))
            self.root.after(0, lambda: self.finish_migration(True))

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"迁移失败: {str(e)}"))
            self.root.after(0, lambda: self.finish_migration(False))

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

    # 设置中文字体
    font_config = ("SimHei", 10)
    root.option_add("*Font", font_config)

    app = GameDataMigrator(root)
    root.mainloop()