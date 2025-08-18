import os
import platform

def get_folder_size(path):
    total_size = 0
    error_msg = ""
    try:
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                # 跳过符号链接和无法访问的文件
                if os.path.islink(file_path):
                    continue
                try:
                    total_size += os.path.getsize(file_path)
                except (PermissionError, FileNotFoundError):
                    error_msg = "部分文件无法访问，大小可能不准确"
                    continue
    except PermissionError:
        return 0, "无权限访问该文件夹"
    except Exception as e:
        return 0, f"计算大小失败: {str(e)}"

    # 转换为MB并保留两位小数
    size_mb = round(total_size / (1024 * 1024), 2)
    return size_mb, error_msg


# noinspection SpellCheckingInspection
def find_target_directories(target_rel_path):

    found_dirs = []

    # 获取系统根目录
    if platform.system() == 'Windows':
        roots = []
        for drive in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive_path = f'{drive}:\\'
            if os.path.exists(drive_path):
                roots.append(drive_path)
    else:
        roots = ['/']

    # 遍历搜索
    find_path_count = 0
    for root in roots:
        print(f"正在搜索: {root}...")
        for dirpath, _, _ in os.walk(root):
            try:
                # 检查目标路径是否存在
                target_path = os.path.join(dirpath, target_rel_path)
                if os.path.isdir(target_path):
                    # 计算找到的文件夹大小
                    find_path_count += 1
                    size_mb, error_msg = get_folder_size(target_path)
                    found_dirs.append((target_path, size_mb, error_msg))
                    print(f"<{find_path_count}>  找到: {target_path} (大小: {size_mb} MB)")
            except PermissionError:
                continue
            except Exception as e:
                print(f"访问目录 {dirpath} 时出错: {str(e)}")
                continue

    return found_dirs