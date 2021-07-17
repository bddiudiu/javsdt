# -*- coding:utf-8 -*-
import os
from os import sep
from configparser import RawConfigParser
from shutil import copyfile

from aip import AipBodyAnalysis

# 设置
from Car import find_car_library, find_car_fc2
from JavFile import JavFile


class Settings(object):
    def __init__(self, pattern):
        self._pattern = pattern
        config_settings = RawConfigParser()
        config_settings.read('【点我设置整理规则】.ini', encoding='utf-8-sig')
        ####################################################### nfo ###################################################
        # 是否 跳过已存在nfo的文件夹，不处理已有nfo的文件夹
        self.bool_skip = True if config_settings.get("收集nfo", "是否跳过已存在nfo的文件夹？") == '是' else False
        # 是否 收集nfo
        self.bool_nfo = True if config_settings.get("收集nfo", "是否收集nfo？") == '是' else False
        # 自定义 nfo中title的格式
        self.list_name_nfo_title = config_settings.get("收集nfo", "nfo中title的格式").replace('标题', '完整标题', 1).split('+')
        # 是否 去除 标题 末尾可能存在的演员姓名
        self.bool_strip_actors = True if config_settings.get("收集nfo", "是否去除标题末尾的演员姓名？") == '是' else False
        # 自定义 将系列、片商等元素作为特征，因为emby不会直接在影片介绍页面上显示片商，也不会读取系列set
        self._custom_genres = config_settings.get("收集nfo", "额外将以下元素添加到特征中").split('、') if config_settings.get("收集nfo",
                                                                                                              "额外将以下元素添加到特征中") else []
        # 自定义 将系列、片商等元素作为特征，因为emby不会直接在影片介绍页面上显示片商，也不会读取系列set
        self._list_extra_genres = [i for i in self._custom_genres if i != '系列' and i != '片商']
        # ？是否将“系列”写入到特征中
        self.bool_write_series = True if '系列' in self._custom_genres else False
        # ？是否将“片商”写入到特征中
        self.bool_write_studio = True if '片商' in self._custom_genres else False
        # 是否 将特征保存到风格中
        self.bool_genre = True if config_settings.get("收集nfo", "是否将特征保存到genre？") == '是' else False
        # 是否 将 片商 作为特征
        self.bool_tag = True if config_settings.get("收集nfo", "是否将特征保存到tag？") == '是' else False
        ####################################################### 重命名 #################################################
        # 是否 重命名 视频
        self.bool_rename_video = True if config_settings.get("重命名影片", "是否重命名影片？") == '是' else False
        # 自定义 重命名 视频
        self._list_rename_video = config_settings.get("重命名影片", "重命名影片的格式").split('+')
        # 是否 重命名视频所在文件夹，或者为它创建独立文件夹
        self._bool_rename_folder = True if config_settings.get("修改文件夹", "是否重命名或创建独立文件夹？") == '是' else False
        # 自定义 新的文件夹名  示例：['车牌', '【', '全部演员', '】']
        self._list_rename_folder = config_settings.get("修改文件夹", "新文件夹的格式").split('+')
        ########################################################## 归类 ################################################
        # 是否 归类jav
        self.bool_classify = True if config_settings.get("归类影片", "是否归类影片？") == '是' else False
        # 是否 针对“文件夹”归类jav，“否”即针对“文件”
        self.bool_classify_folder = True if config_settings.get("归类影片", "针对文件还是文件夹？") == '文件夹' else False
        # 自定义 路径 归类的jav放到哪
        self._custom_classify_target_dir = config_settings.get("归类影片", "归类的根目录")
        # 自定义 jav按什么类别标准来归类 比如：影片类型\全部演员
        self._custom_classify_basis = config_settings.get("归类影片", "归类的标准")
        ######################################################## 图片 ################################################
        # 是否 下载图片
        self.bool_jpg = True if config_settings.get("下载封面", "是否下载封面海报？") == '是' else False
        # 自定义 命名 大封面fanart
        self.list_name_fanart = config_settings.get("下载封面", "DVD封面的格式").split('+')
        # 自定义 命名 小海报poster
        self.list_name_poster = config_settings.get("下载封面", "海报的格式").split('+')
        # 是否 如果视频有“中字”，给poster的左上角加上“中文字幕”的斜杠
        self.bool_watermark_subtitle = True if config_settings.get("下载封面", "是否为海报加上中文字幕条幅？") == '是' else False
        # 是否 如果视频是“无码流出”，给poster的右上角加上“无码流出”的斜杠
        self.bool_watermark_divulge = True if config_settings.get("下载封面", "是否为海报加上无码流出条幅？") == '是' else False
        ###################################################### 字幕 #######################################################
        # 是否 重命名用户已拥有的字幕
        self.bool_rename_subtitle = True if config_settings.get("字幕文件", "是否重命名已有的字幕文件？") == '是' else False
        ###################################################### kodi #######################################################
        # 是否 收集演员头像
        self.bool_sculpture = True if config_settings.get("kodi专用", "是否收集演员头像？") == '是' else False
        # 是否 对于多cd的影片，kodi只需要一份图片和nfo
        self.bool_cd_only = True if config_settings.get("kodi专用", "是否对多cd只收集一份图片和nfo？") == '是' else False
        ###################################################### 代理 ########################################################
        # 代理端口
        self._custom_proxy = config_settings.get("局部代理", "代理端口").strip()
        # 是否 使用局部代理
        self._bool_proxy = True if config_settings.get("局部代理", "是否使用局部代理？") == '是' and self._custom_proxy else False
        # 代理，如果为空则效果为不使用
        self._proxys_ = {'http': f'http://{self._custom_proxy}', 'https': f'https://{self._custom_proxy}'} \
            if config_settings.get("局部代理", "http还是socks5？") == '是' and self._custom_proxy \
            else {'http': f'socks5://{self._custom_proxy}', 'https': f'socks5://{self._custom_proxy}'}
        # 是否 代理javlibrary
        self.proxy_library = self._proxys if config_settings.get("局部代理", "是否代理javlibrary（有问题）？") == '是' else {}
        # 是否 代理javbus，还有代理javbus上的图片cdnbus
        self.proxy_bus = self._proxys if config_settings.get("局部代理", "是否代理javbus？") == '是' else {}
        # 是否 代理javbus，还有代理javbus上的图片cdnbus
        self.proxy_321 = self._proxys if config_settings.get("局部代理", "是否代理jav321？") == '是' else {}
        # 是否 代理javdb，还有代理javdb上的图片
        self.proxy_db = self._proxys if config_settings.get("局部代理", "是否代理javdb？") == '是' else {}
        # 是否 代理arzon
        self.proxy_arzon = self._proxys if config_settings.get("局部代理", "是否代理arzon？") == '是' else {}
        # 是否 代理dmm图片，javlibrary和javdb上的有码图片几乎都是直接引用dmm
        self.proxy_dmm = self._proxys if config_settings.get("局部代理", "是否代理dmm图片？") == '是' else {}
        #################################################### 原影片文件的性质 ################################################
        # 自定义 无视的字母数字 去除影响搜索结果的字母数字 xhd1080、mm616、FHD-1080
        self._list_surplus_words_in_filename = config_settings.get("原影片文件的性质", "有码素人无视多余的字母数字").upper().split('、') \
            if self._pattern == '有码' \
            else config_settings.get("原影片文件的性质", "无码无视多余的字母数字").upper().split('、')
        # 自定义 原影片性质 影片有中文，体现在视频名称中包含这些字符
        self._custom_subtitle_words_in_filename = config_settings.get("原影片文件的性质", "是否中字即文件名包含")
        # 自定义 是否中字 这个元素的表现形式
        self.custom_subtitle_expression = config_settings.get("原影片文件的性质", "是否中字的表现形式")
        # 自定义 原影片性质 影片是无码流出片，体现在视频名称中包含这些字符
        self._custom_divulge_words_in_filename = config_settings.get("原影片文件的性质", "是否流出即文件名包含")
        # 自定义 是否流出 这个元素的表现形式
        self.custom_divulge_expression = config_settings.get("原影片文件的性质", "是否流出的表现形式")
        # 自定义 原影片性质 有码
        self._av_type = config_settings.get("原影片文件的性质", self._pattern)
        ##################################################### 信息来源 ##################################################
        # 是否 收集javlibrary下方用户超过10个人点赞的评论
        self.bool_review = True if config_settings.get("信息来源", "是否用javlibrary整理影片时收集网友的热评？") == '是' else False
        ################################################### 其他设置 ####################################################
        # 是否 使用简体中文 简介翻译的结果和jav特征会变成“简体”还是“繁体”
        self.bool_zh = True if config_settings.get("其他设置", "简繁中文？") == '简' else False
        # 网址 javlibrary
        self.url_library = f'{config_settings.get("其他设置", "javlibrary网址").strip().rstrip("/")}/cn'
        # 网址 javbus
        self.url_bus = config_settings.get("其他设置", "javbus网址").strip().rstrip('/')
        # 网址 javdb
        self.url_db = config_settings.get("其他设置", "javdb网址").strip().rstrip('/')
        # 自定义 文件类型 只有列举出的视频文件类型，才会被处理
        self._tuple_video_types = config_settings.get("其他设置", "扫描文件类型").upper().split('、')
        # 自定义 命名格式中“标题”的长度 windows只允许255字符，所以限制长度，但nfo中的标题是全部
        self.int_title_len = int(config_settings.get("其他设置", "重命名中的标题长度（50~150）"))
        ######################################## 百度翻译API ####################################################
        # 是否 把日语简介翻译为中文
        self.bool_tran = True if config_settings.get("百度翻译API", "是否翻译为中文？") == '是' else False
        # 账户 百度翻译api
        self._tran_id = config_settings.get("百度翻译API", "APP ID")
        self._tran_sk = config_settings.get("百度翻译API", "密钥")
        ######################################## 百度人体分析 ####################################################
        # 是否 需要准确定位人脸的poster
        self.bool_face = True if config_settings.get("百度人体分析", "是否需要准确定位人脸的poster？") == '是' else False
        # 账户 百度人体分析
        self._al_id = config_settings.get("百度人体分析", "appid")
        self._ai_ak = config_settings.get("百度人体分析", "api key")
        self._al_sk = config_settings.get("百度人体分析", "secret key")

        self.dict_for_standard, self.list_classify_basis = self.get_dict_for_standard()

    # #########################[修改文件夹]##############################
    # 是否需要重命名文件夹或者创建新的文件夹
    def judge_need_rename_folder(self):
        if self.bool_classify:  # 如果需要归类
            if self.bool_classify_folder:  # 并且是针对文件夹
                return True  # 那么必须重命名文件夹或者创建新的文件夹
            else:
                return False  # 否则不会操作新文件夹
        else:  # 不需要归类
            if self._bool_rename_folder:  # 但是用户本来就在ini中写了要重命名文件夹
                return True
            else:
                return False

    # #########################[归类影片]##############################
    # 功能：如果需要为kodi整理头像，则先检查“演员头像for kodi.ini”、“演员头像”文件夹是否存在; 检查 归类根目录 的合法性
    # 参数：是否需要整理头像，用户自定义的归类根目录，用户选择整理的文件夹路径
    # 返回：归类根目录路径
    # 辅助：os.sep，os.path.exists，os.system，shutil.copyfile
    def init_check(self, dir_choose):
        # 检查头像: 如果需要为kodi整理头像，先检查演员头像ini、头像文件夹是否存在。
        if self.bool_sculpture:
            if not os.path.exists('演员头像'):
                print('\n“演员头像”文件夹丢失！请把它放进exe的文件夹中！\n')
                os.system('pause')
            if not os.path.exists('【缺失的演员头像统计For Kodi】.ini'):
                if os.path.exists('actors_for_kodi.ini'):
                    copyfile('actors_for_kodi.ini', '【缺失的演员头像统计For Kodi】.ini')
                    print('\n“【缺失的演员头像统计For Kodi】.ini”成功！')
                else:
                    print('\n请打开“【ini】重新创建ini.exe”创建丢失的程序组件!')
                    os.system('pause')
        if self.bool_classify:
            custom_classify_target_dir = self._custom_classify_target_dir.rstrip(sep)
            # 用户使用默认的“所选文件夹”
            if custom_classify_target_dir == '所选文件夹':
                return f'{dir_choose}{sep}归类完成'
            # 归类根目录 是 用户输入的路径c:\a，继续核实合法性
            else:
                # 用户输入的路径 不是 所选文件夹dir_choose
                if custom_classify_target_dir != dir_choose:
                    if custom_classify_target_dir[:2] != dir_choose[:2]:
                        print('归类的根目录“', custom_classify_target_dir, '”和所选文件夹不在同一磁盘无法归类！请修正！')
                        os.system('pause')
                    if not os.path.exists(custom_classify_target_dir):
                        print('归类的根目录“', custom_classify_target_dir, '”不存在！无法归类！请修正！')
                        os.system('pause')
                    return custom_classify_target_dir
                # 用户输入的路径 就是 所选文件夹dir_choose
                else:
                    return f'{dir_choose}{sep}归类完成'
        else:
            return ''

    # #########################[原影片文件的性质]##############################
    # 得到代表中字的文字list
    def list_subtitle_word_in_filename(self):
        return self._custom_subtitle_words_in_filename.upper().split('、')

    # 得到代表流出的文字list
    def list_divulge_word_in_filename(self):
        return self._custom_divulge_words_in_filename.upper().split('、')

    # #########################[其他设置]##############################
    # jav321网址
    def get_url_321(self):
        if self.bool_zh:
            url_search_321 = 'https://www.jav321.com/search'
            url_web_321 = 'https://www.jav321.com'
        else:
            url_search_321 = 'https://tw.jav321.com/search'
            url_web_321 = 'https://tw.jav321.com'
        return url_search_321, url_web_321

    # #########################[百度翻译API]##############################
    # 百度翻译的目标语言、翻译账户
    def get_translate_account(self):
        if self.bool_zh:
            to_language = 'zh'  # 目标语言，zh是简体中文，cht是繁体中文
        else:
            to_language = 'cht'
        return to_language, self._tran_id, self._tran_sk

    # #########################[百度人体分析]##############################
    def start_body_analysis(self):
        if self.bool_face:
            return AipBodyAnalysis(self._al_id, self._ai_ak, self._al_sk)
        else:
            return None

    # 功能：完善用于命名的dict_data，如果用户自定义的各种命名公式中有dict_data未包含的元素，则添加进dict_data。
    #      将可能比较复杂的list_classify_basis按“+”“\”切割好，准备用于组装后面的归类路径。
    # 参数：用户自定义的各种命名公式list
    # 返回：存储命名信息的dict_data， 切割好的归类标准list_classify_basis
    # 辅助：os.sep
    def get_dict_for_standard(self):
        if self._pattern == '无码':
            dict_for_standard = {'车牌': 'CBA-123',
                                 '车牌前缀': 'CBA',
                                 '标题': '无码标题',
                                 '完整标题': '完整无码标题',
                                 '导演': '无码导演',
                                 '制作商': '无码制作商',
                                 '发行商': '无码发行商',
                                 '评分': '0',
                                 '片长': '0',
                                 '系列': '无码系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': '无码演员', '全部演员': '无码演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'CBA-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'CBA-123', '原文件夹名': 'CBA-123', }
        elif self._pattern == '素人':
            dict_for_standard = {'车牌': 'XYZ-123',
                                 '车牌前缀': 'XYZ',
                                 '标题': '素人标题',
                                 '完整标题': '完整素人标题',
                                 '导演': '素人导演',
                                 '制作商': '素人制作商',
                                 '发行商': '素人发行商',
                                 '评分': '0',
                                 '片长': '0',
                                 '系列': '素人系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': '素人演员', '全部演员': '素人演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'XYZ-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'XYZ-123', '原文件夹名': 'XYZ-123', }
        elif self._pattern == 'fc2':
            dict_for_standard = {'车牌': 'FC2-123',
                                 '车牌前缀': 'FC2',
                                 '标题': 'FC2标题',
                                 '完整标题': '完整FC2标题',
                                 '导演': 'FC2导演',
                                 '制作商': 'fc2制作商',
                                 '发行商': 'fc2发行商',
                                 '评分': '0',
                                 '片长': '0',
                                 '系列': 'FC2系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': 'FC2演员', '全部演员': 'FC2演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'FC2-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'FC2-123', '原文件夹名': 'FC2-123', }
        else:
            dict_for_standard = {'车牌': 'ABC-123',
                                 '车牌前缀': 'ABC',
                                 '标题': '有码标题',
                                 '完整标题': '完整有码标题',
                                 '导演': '有码导演',
                                 '制作商': '有码制作商',
                                 '发行商': '有码发行商',
                                 '评分': '0',
                                 '片长': '0',
                                 '系列': '有码系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': '有码演员', '全部演员': '有码演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'ABC-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'ABC-123', '原文件夹名': 'ABC-123', }
        for i in self._list_extra_genres:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self._list_rename_video:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self._list_rename_folder:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self.list_name_nfo_title:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self.list_name_fanart:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self.list_name_poster:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        list_classify_basis = []
        for i in self._custom_classify_basis.split('\\'):
            for j in i.split('+'):
                if j not in dict_for_standard:
                    dict_for_standard[j] = j
                list_classify_basis.append(j)
            list_classify_basis.append(sep)
        return dict_for_standard, list_classify_basis

    def get_dict_subtitle_file(self, list_sub_files, list_suren_cars):
        dict_subtitle_file = {}
        if self._pattern == 'Fc2':
            for file_raw in list_sub_files:
                file_temp = file_raw.upper()
                if file_temp.endswith(('.SRT', '.VTT', '.ASS', '.SSA', '.SUB', '.SMI',)):
                    # 仅处理fc2
                    if 'FC2' not in file_temp:
                        continue  # 【跳出2】
                    # 得到字幕文件名中的车牌
                    subtitle_car = find_car_fc2(file_temp)
                    if subtitle_car:
                        dict_subtitle_file[file_raw] = subtitle_car
        else:
            for file_raw in list_sub_files:
                file_temp = file_raw.upper()
                if file_temp.endswith(('.SRT', '.VTT', '.ASS', '.SSA', '.SUB', '.SMI',)):
                    # 当前模式不处理FC2
                    if 'FC2' in file_temp:
                        continue
                    # 去除用户设置的、干扰车牌的文字
                    for word in self._list_surplus_words_in_filename:
                        file_temp = file_temp.replace(word, '')
                    # 得到字幕文件名中的车牌
                    subtitle_car = find_car_library(file_temp, list_suren_cars)
                    # 将该字幕文件和其中的车牌对应到dict_subtitle_file中
                    if subtitle_car:
                        dict_subtitle_file[file_raw] = subtitle_car
        return dict_subtitle_file

    def get_list_jav_structs(self, list_sub_files, no_current, list_suren_cars, dict_subtitle_file, dir_current,
                             dir_current_relative):
        list_jav_structs = []  # 存放: 需要整理的jav的结构体
        dict_car_episode = {}  # 存放: 每一车牌的集数， 例如{'abp-123': 1, avop-789': 2}是指 abp-123只有一集，avop-789有cd1、cd2
        for file_raw in list_sub_files:
            file_temp = file_raw.upper()
            if file_temp.endswith(self._tuple_video_types) and not file_temp.startswith('.'):
                no_current += 1
                if 'FC2' in file_temp:
                    continue
                for word in self._list_surplus_words_in_filename:
                    file_temp = file_temp.replace(word, '')
                # 得到视频中的车牌
                car = find_car_library(file_temp, list_suren_cars)
                if car:
                    try:
                        dict_car_episode[car] += 1  # 已经有这个车牌了，加一集cd
                    except KeyError:
                        dict_car_episode[car] = 1  # 这个新车牌有了第一集
                    # 这个车牌在dict_subtitle_files中，有它的字幕。
                    if car in dict_subtitle_file.values():
                        subtitle_file = list(dict_subtitle_file.keys())[list(dict_subtitle_file.values()).index(car)]
                        del dict_subtitle_file[subtitle_file]
                    else:
                        subtitle_file = ''
                    # 将该jav的各种属性打包好，包括原文件名带扩展名、所在文件夹路径、第几集、所属字幕文件名
                    jav_struct = JavFile(file_raw, dir_current, car, dict_car_episode[car], subtitle_file, no_current)
                    list_jav_structs.append(jav_struct)
                else:
                    print(f'>>无法处理: {dir_current_relative}{sep}{file_raw}')
        return list_jav_structs, dict_car_episode

    # 功能：所选文件夹总共有多少个视频文件
    # 参数：用户选择整理的文件夹路径dir_choose
    # 返回：无
    # 辅助：os.walk
    def count_num_videos(self, dir_choose):
        num_videos = 0
        for dir_current, list_sub_dirs, list_sub_files in os.walk(dir_choose):
            for file_raw in list_sub_files:
                file_temp = file_raw.upper()
                if file_temp.endswith(self._tuple_video_types) and not file_temp.startswith('.'):
                    num_videos += 1
        return num_videos
