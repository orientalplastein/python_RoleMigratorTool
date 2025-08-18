import os
import shutil
from find_paths import find_target_directories

# noinspection SpellCheckingInspection
foundPaths = find_target_directories(r'SeasunGame\Game')

path_select = input("选择游戏路径——第__个:")
try:
    path_selected = foundPaths[int(path_select)-1][0]
except ValueError:
    print('请输入正确的序号')
# noinspection PyUnboundLocalVariable
print(path_selected)

version_select = input("<1>  正式服\n<2>  测试服\n选择游戏版本:")
try:
    version_select = int(version_select)
    if version_select == 1:
        game_path = os.path.join(path_selected, 'JX3')
    elif version_select == 2:
        game_path = os.path.join(path_selected, 'JX3_EXP')
except ValueError:
    print('请输入正确的序号')

# 筛选出有数据的角色
# noinspection PyUnboundLocalVariable
userdata_path = os.path.join(game_path,r'bin\zhcn_hd\userdata')
valid_user = []
for user in os.listdir(userdata_path):
    if len(user)>=4 and '.dat' not in user:
        # print(os.listdir(os.path.join(userdata_path,user)))
        if '电信区' in os.listdir(os.path.join(userdata_path,user)) or '双线区' in os.listdir(os.path.join(userdata_path,user)) or '无界区' in os.listdir(os.path.join(userdata_path,user)) :
            valid_user.append(user)

#遍历用户_大区_服务器_角色
# noinspection SpellCheckingInspection
countSeqInuserdataPath = userdata_path.count('\\')
user_server_serverIndex_rolePath  = []
for user in valid_user:
    current_user_path = os.path.join(userdata_path,user)
    for a,b,c in os.walk(current_user_path):
        if a.count('\\') - countSeqInuserdataPath == 4:
            user_server_serverIndex_rolePath.append(a) #结果有序

#按账号分类打印显示
for user in valid_user:
    for user_s in user_server_serverIndex_rolePath:
        user_seq = '\\'+user+'\\'
        if  user_seq in user_s:
            print(f'<{user_server_serverIndex_rolePath.index(user_s)+1}>  {user_s}')
    print('--------------------------------')

#确认源角色和目标角色，源->目标
role_origin2target = list(map(int,input("输入源角色序号和目标角色序号，以空格分割: ").split(' ')))
origin_role = user_server_serverIndex_rolePath[role_origin2target[0]-1].rsplit('\\',1)[-1]
target_role = user_server_serverIndex_rolePath[role_origin2target[1]-1].rsplit('\\',1)[-1]
print(f'源角色<{origin_role}> , 目标角色<{target_role}>')

#进行文件夹复制操作，源->目标
try:
    shutil.copytree(user_server_serverIndex_rolePath[role_origin2target[0]-1],user_server_serverIndex_rolePath[role_origin2target[1]-1],dirs_exist_ok=True)
except ValueError:
    print('请输入正确的序号')
print('不出意外的话，数据迁移完成')