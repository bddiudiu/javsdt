# -*- coding:utf-8 -*-
import os
import re
from shutil import copyfile
from traceback import format_exc

#################################################### 相同 ##############################################################
from Class.Settings import Settings
from Class.JavFile import JavFile
from Status import judge_exist_nfo, count_num_videos, judge_separate_folder
from User import choose_directory
from Record import record_start, record_fail
from Prepare import perfect_dict_data
from Standard import rename_mp4, rename_folder, classify_files, classify_folder
from XML import replace_xml, replace_xml_win
from Prepare import judge_exist_subtitle
from Picture import check_picture, add_watermark_subtitle
from Download import download_pic
# from Functions.Genre import better_dict_genre
from Car import list_suren_car
# ################################################## 部分不同 ##########################################################
from Prepare import judge_exist_divulge
from Status import check_actors
from Baidu import translate
from Picture import add_watermark_divulge, crop_poster_default
# ################################################## 独特 ##########################################################
from Car import find_car_suren
from Functions.Web.Jav321 import get_321_html, post_321_html


#  main开始
print('1、请开启代理，建议美国节点，访问“https://www.jav321.com/”\n'
      '2、影片信息没有导演，没有演员头像，可能没有演员姓名\n'
      '3、只能整理列出车牌的素人影片\n'
      '   如有素人车牌识别不出，请在ini中添加该车牌，或者告知作者\n')

# 读取配置文件，这个ini文件用来给用户设置
print('正在读取ini中的设置...', end='')
try:
    settings = Settings('素人')
except:
    settings = None
    print(format_exc())
    print('\n无法读取ini文件，请修改它为正确格式，或者打开“【ini】重新创建ini.exe”创建全新的ini！')
    os.system('pause')
print('\n读取ini文件成功!\n')

# 路径分隔符: 当前系统的路径分隔符 windows是“\”，linux和mac是“/”
sep = os.sep

# 检查头像: 如果需要为kodi整理头像，先检查演员头像ini、头像文件夹是否存在。
check_actors(settings.bool_sculpture)

# 局部代理: 哪些站点需要代理。
proxy_library, proxy_bus, proxy_321, proxy_db, proxy_arzon, proxy_dmm = settings.get_proxy()
# jav321网址 搜索网址 https://www.jav321.com/search https://www.jav321.com/
url_search, url_321 = settings.get_url_321()

# 选择简繁中文以及百度翻译账户: 需要简体中文还是繁体中文，影响影片特征和简介。
to_language, tran_id, tran_sk = settings.get_translate_account()

# 信息字典: 存放影片信息，用于给用户自定义各种命名。
dict_data = settings.get_dict_for_standard()

# nfo中title的写法。
list_name_nfo_title = settings.formula_name_nfo_title()
# 额外将哪些元素放入特征中
list_extra_genres = settings.list_extra_genre()
# 重命名视频的格式
list_name_video = settings.formula_rename_video()
# 重命名文件夹的格式
list_name_folder = settings.formula_rename_folder()

# fanart的格式
list_name_fanart = settings.formula_name_fanart()
# poster的格式
list_name_poster = settings.formula_name_poster()

# 视频文件名包含哪些多余的字母数字，需要无视
list_surplus_words_in_filename = settings.list_surplus_word_in_filename()
# 文件名包含哪些特殊含义的文字，判断是否中字
list_subtitle_words_in_filename = settings.list_subtitle_word_in_filename()
# 文件名包含哪些特殊含义的文字，判断是否是无码流出片
list_divulge_words_in_filename = settings.list_divulge_word_in_filename()

# 素人番号: 得到事先设置的素人番号，让程序能跳过它们
list_suren_cars = list_suren_car()

# 需要扫描的文件的类型
tuple_video_types = settings.tuple_video_type()

# 完善dict_data，如果用户自定义了一些文字，不在元素中，需要将它们添加进dict_data；list_classify_basis，归类标准，归类目标文件夹的组成公式。
dict_data, list_classify_basis = perfect_dict_data(list_extra_genres, list_name_video, list_name_folder,
                                                   list_name_nfo_title, list_name_fanart, list_name_poster,
                                                   settings.custom_classify_basis(), dict_data)

# 是否需要重命名文件夹
bool_rename_folder = settings.judge_need_rename_folder()

# 用户输入“回车”就继续选择文件夹整理
input_start_key = ''
while input_start_key == '':
    # 用户: 选择需要整理的文件夹
    dir_choose = choose_directory()
    # 日志: 在txt中记录一下用户的这次操作，在某个时间选择了某个文件夹
    record_start(dir_choose)
    # 归类: 用户自定义的归类根目录，如果不需要归类则为空
    dir_classify_target = settings.init_check(dir_choose)
    # 计数: 失败次数及进度
    num_fail = 0  # 已经或可能导致致命错误，比如整理未完成，同车牌有不同视频
    num_current = 0  # 当前视频的编号
    sum_all_videos = count_num_videos(dir_choose, tuple_video_types)  # 所选文件夹总共有多少个视频文件
    print('...文件扫描开始...如果时间过长...请避开夜晚高峰期...\n')
    # dir_current【当前所处文件夹】 list_sub_dirs【子文件夹们】 list_sub_files【子文件们】
    for dir_current, list_sub_dirs, list_sub_files in os.walk(dir_choose):
        # 什么文件都没有
        if not list_sub_files:
            continue
        # 当前directory_current是已归类的目录，无需处理
        dir_current_relative = dir_current[len(dir_choose):]    # 当前所处文件夹 相对于 所选文件夹 的路径，用于报错
        if '归类完成' in dir_current_relative:
            continue
        # 跳过已存在nfo的文件夹，判断这一层文件夹中有没有nfo
        if settings.bool_skip and judge_exist_nfo(list_sub_files):
            continue
        # 对这一层文件夹进行评估,有多少视频，有多少同车牌视频，是不是独立文件夹
        list_jav_struct = []  # 存放: 需要整理的jav的结构体
        dict_car_episode = {}  # 存放: 每一车牌的集数， 例如{'abp-123': 1, avop-789': 2}是指 abp-123只有一集，avop-789有cd1、cd2
        num_videos_include = 0  # 计数: 当前文件夹中视频的数量，可能有视频不是jav
        dict_subtitle_files = {}  # 存放: jav的字幕文件和车牌对应关系 {'c:\a\abc_123.srt': 'abc-123'}
        # 判断文件是不是字幕文件，放入dict_subtitle_files中
        for file_raw in list_sub_files:
            file_temp = file_raw.upper()
            if file_temp.endswith(('.SRT', '.VTT', '.ASS', '.SSA', '.SUB', '.SMI',)):
                # 当前模式不处理FC2
                if 'FC2' in file_temp:
                    continue
                # 去除用户设置的、干扰车牌的文字
                for word in list_surplus_words_in_filename:
                    file_temp = file_temp.replace(word, '')
                # 得到字幕文件名中的车牌
                subtitle_car = find_car_suren(file_temp, list_suren_cars)
                # 将该字幕文件和其中的车牌对应到dict_subtitle_files中
                if subtitle_car:
                    dict_subtitle_files[file_raw] = subtitle_car
        # print(dict_subtitle_files)
        # 判断文件是不是视频，放入list_jav_struct中
        for file_raw in list_sub_files:
            file_temp = file_raw.upper()
            if file_temp.endswith(tuple_video_types) and not file_temp.startswith('.'):
                num_videos_include += 1
                num_current += 1
                if 'FC2' in file_temp:
                    continue
                for word in list_surplus_words_in_filename:
                    file_temp = file_temp.replace(word, '')
                # 得到视频中的车牌
                car = find_car_suren(file_temp, list_suren_cars)
                if car:
                    try:
                        dict_car_episode[car] += 1  # 已经有这个车牌了，加一集cd
                    except KeyError:
                        dict_car_episode[car] = 1  # 这个新车牌有了第一集
                    # 这个车牌在dict_subtitle_files中，有它的字幕。
                    if car in dict_subtitle_files.values():
                        subtitle_file = list(dict_subtitle_files.keys())[list(dict_subtitle_files.values()).index(car)]
                        del dict_subtitle_files[subtitle_file]
                    else:
                        subtitle_file = ''
                    # 将该jav的各种属性打包好，包括原文件名带扩展名、所在文件夹路径、第几集、所属字幕文件名
                    jav_struct = JavFile(file_raw, dir_current, car, dict_car_episode[car], subtitle_file, num_current)
                    list_jav_struct.append(jav_struct)
                else:
                    print(f'>>无法处理: {dir_current_relative}{sep}{file_raw}')

        # 判定影片所在文件夹是否是独立文件夹，独立文件夹是指该文件夹仅用来存放该影片，而不是大杂烩文件夹
        # 这一层文件夹下有jav
        if dict_car_episode:
            bool_separate_folder = judge_separate_folder(len(dict_car_episode), num_videos_include,
                                                         len(list_jav_struct), list_sub_dirs)
        else:
            continue

        # 开始处理每一部jav
        for jav in list_jav_struct:
            # region 相同
            # 告诉用户进度
            print(f'>> [{str(jav.number)}/{str(sum_all_videos)}]:{jav.name}')
            print(f'    >发现车牌: {jav.car}')

            # 判断是否有中字的特征，条件有三满足其一即可: 1有外挂字幕 2文件名中含有“-C”之类的字眼 3旧的nfo中已经记录了它的中字特征
            if jav.subtitle:
                bool_subtitle = True  # 判定成功
                dict_data['是否中字'] = settings.custom_subtitle_expression  # '是否中字'这一命名元素被激活
            else:
                bool_subtitle = judge_exist_subtitle(dir_current, jav.name_no_ext, list_subtitle_words_in_filename)
                dict_data['是否中字'] = settings.custom_subtitle_expression if bool_subtitle else ''
            # 判断是否是无码流出的作品，同理
            bool_divulge = judge_exist_divulge(dir_current, jav.name_no_ext, list_divulge_words_in_filename)
            dict_data['是否流出'] = settings.custom_divulge_expression if bool_divulge else ''

            path_relative = jav.path[len(dir_choose):]     # 影片的相对于所选文件夹的路径，用于报错
            # endregion

            # 获取nfo信息的jav321网页
            try:
                # 用户指定了网址，则直接得到jav所在网址
                if '图书馆' in jav.name:
                    url_appointg = re.search(r'三二一(.+?)\.', jav.name)
                    if url_appointg:
                        url_jav = f'{url_321}/video/{url_appointg.group(1)}'
                        print('    >获取信息: ', url_jav)
                        html_web = get_321_html(url_jav, proxy_321)
                        # 尝试找标题，jav321上的标题不包含车牌，title_only表示单纯的标题
                        titleg = re.search(r'<h3>(.+?) <small>', html_web)  # 匹配处理“标题”
                        # 就是AV的页面
                        if titleg:
                            title_only = titleg.group(1)
                            print(title_only)
                        # 找不到标题，jav321找不到影片
                        else:
                            # print(html_web)
                            num_fail += 1
                            record_fail(f'    >第{num_fail}个失败！你指定的jav321网址有错误: {path_relative}\n')
                            continue  # 【退出对该jav的整理】
                    else:
                        num_fail += 1
                        record_fail(f'    >第{num_fail}个失败！你指定的jav321网址有错误: {path_relative}\n')
                        continue  # 【退出对该jav的整理】
                # 用户没有指定网址，则去搜索
                else:
                    # 得到jav321搜索网页html
                    print(f'    >搜索车牌: {url_search}')
                    html_web = post_321_html(url_search, {'sn': jav.car}, proxy_321)
                    # print(html_web)
                    # 尝试找标题
                    titleg = re.search(r'h3>(.+?) <small>', html_web)  # 匹配处理“标题”
                    # 找得到，搜索结果就是AV的页面
                    if titleg:
                        title_only = titleg.group(1)
                        # print(title_only)
                    # 找不到标题，jav321找不到影片
                    else:
                        num_fail += 1
                        record_fail(f'    >第{num_fail}个失败！jav321找不到该车牌的信息: {jav.car}，{path_relative}\n')
                        continue  # 【退出对该jav的整理】

                # 去除xml文档和windows路径不允许的特殊字符 &<>  \/:*?"<>|
                title_only = replace_xml_win(title_only)
                # 正则匹配 影片信息 开始！
                # 有大部分信息的html_web
                html_web = re.search(r'(h3>.+?)async', html_web).group(1)
                # print(html_web)
                # 车牌
                dict_data['车牌'] = car = re.search(r'番.?</b>: (.+?)<br>', html_web).group(1).upper()
                dict_data['车牌前缀'] = car.split('-')[0]
                # jav321上素人的title开头不是车牌
                title = f'{car} {title_only}'
                # 给用户重命名用的标题是“短标题”，nfo中是“完整标题”，但用户在ini中只用写“标题”
                dict_data['完整标题'] = title_only
                # 处理影片的标题过长
                if len(title_only) > settings.int_title_len:
                    dict_data['标题'] = title_only[:settings.int_title_len]
                else:
                    dict_data['标题'] = title_only
                print('    >影片标题: ', title)
                # DVD封面cover
                coverg = re.search(r'poster="(.+?)"><source', html_web)  # 封面图片的正则对象
                if coverg:
                    url_cover = coverg.group(1)
                else:  # src="http://pics.dmm.co.jp/digital/amateur/scute530/scute530jp-001.jpg"
                    coverg = re.search(r'img-responsive" src="(.+?)"', html_web)  # 封面图片的正则对象
                    if coverg:
                        url_cover = coverg.group(1)
                    else:  # src="http://pics.dmm.co.jp/digital/amateur/scute530/scute530jp-001.jpg"
                        coverg = re.search(r'src="(.+?)"', html_web)  # 封面图片的正则对象
                        if coverg:
                            url_cover = coverg.group(1)
                        else:
                            url_cover = ''
                # 下载海报 poster
                posterg = re.search(r'img-responsive" src="(.+?)"', html_web)  # 封面图片的正则对象
                if posterg:
                    url_poster = posterg.group(1)
                else:
                    url_poster = ''
                # 发行日期
                premieredg = re.search(r'配信開始日</b>: (\d\d\d\d-\d\d-\d\d)<br>', html_web)
                if premieredg:
                    dict_data['发行年月日'] = time_premiered = premieredg.group(1)
                    dict_data['发行年份'] = time_premiered[0:4]
                    dict_data['月'] = time_premiered[5:7]
                    dict_data['日'] = time_premiered[8:10]
                else:
                    dict_data['发行年月日'] = time_premiered = '1970-01-01'
                    dict_data['发行年份'] = '1970'
                    dict_data['月'] = '01'
                    dict_data['日'] = '01'
                # 片长 <td><span class="text">150</span> 分钟</td>
                runtimeg = re.search(r'収録時間</b>: (\d+)', html_web)
                if runtimeg:
                    dict_data['片长'] = runtimeg.group(1)
                else:
                    dict_data['片长'] = '0'
                # 片商</b>: <a href="/company/%E83%A0%28PRESTIGE+PREMIUM%29/1">プレステージプレミアム(PRESTIGE PREMIUM)</a>
                studiog = re.search(r'メーカー</b>: <a href="/company.+?">(.+?)</a>', html_web)
                if studiog:
                    dict_data['片商'] = studio = replace_xml_win(studiog.group(1))
                else:
                    dict_data['片商'] = '素人片商'
                    studio = ''
                # 演员们 和 # 第一个演员   演员</b>: 花音さん 21歳 床屋さん(家族経営) &nbsp
                actorg = re.search(r'出演者</b>: (.+?) ', html_web)
                if actorg:
                    actor_only = actorg.group(1)    # dcv-141 '紗綾さん/27歳/保育士'
                    list_actor = actor_only.replace('/', ' ').split(' ')  # ['紗綾さん', '27歳', '保育士']
                    list_actor = [i for i in list_actor if i]
                    if list_actor:
                        dict_data['首个演员'] = ' '.join(list_actor)
                    else:
                        dict_data['首个演员'] = '素人'
                    dict_data['全部演员'] = dict_data['首个演员']
                else:
                    dict_data['首个演员'] = dict_data['全部演员'] = '素人'
                # 特点
                genres = re.findall(r'genre.+?">(.+?)</a>', html_web)
                genres = [i for i in genres if i != '标签' and i != '標籤' and i != '素人']  # 这些特征 没有参考意义，为用户删去
                if bool_subtitle:  # 有“中字“，加上特征”中文字幕”
                    genres.append('中文字幕')
                if bool_divulge:  # 是流出无码片，加上特征'无码流出'
                    genres.append('无码流出')
                # print(genres)
                # 评分
                scoreg = re.search(r'平均評価</b>: (\d\.\d)<br>', html_web)
                if scoreg:
                    float_score = float(scoreg.group(1))
                    float_score = (float_score - 2) * 10 / 3
                    if float_score >= 0:
                        score = '%.1f' % float_score
                    else:
                        score = '0'
                else:
                    scoreg = re.search(r'img/(\d\d)\.gif', html_web)
                    if scoreg:
                        float_score = float(scoreg.group(1)) / 10
                        float_score = (float_score - 2) * 10 / 3
                        if float_score >= 0:
                            score = '%.1f' % float_score
                        else:
                            score = '0'
                    else:
                        score = '0'
                dict_data['评分'] = score
                # 烂番茄评分 用上面的评分*10
                criticrating = str(float(score) * 10)
                #######################################################################
                # 简介
                if settings.bool_nfo:
                    plotg = re.search(r'md-12">([^<].+?)</div>', html_web)
                    if plotg:
                        plot = plotg.group(1)
                    else:
                        plot = ''
                    plot = f'{title_only}{plot}'
                    if settings.bool_tran:
                        plot = translate(tran_id, tran_sk, plot, to_language)
                        if plot.startswith('【百度'):
                            num_fail += 1
                            record_fail(f'    >第{num_fail}个失败！翻译简介失败: {path_relative}\n')
                    plot = replace_xml(plot)
                else:
                    plot = ''
                # print(plot)
                #######################################################################
                dict_data['视频'] = dict_data['原文件名'] = jav.name_no_ext  # dict_data['视频']，先定义为原文件名，即将发生变化。
                dict_data['原文件夹名'] = jav.folder
                # 是CD1还是CDn？
                num_all_episodes = dict_car_episode[jav.car]  # 该车牌总共多少集
                str_cd = f'-cd{jav.episode}' if num_all_episodes > 1 else ''

                # 1重命名视频【相同】
                try:
                    dict_data, jav, num_temp = rename_mp4(jav, num_fail, settings, dict_data, list_name_video,
                                                          path_relative, str_cd)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

                # 2 归类影片【相同】只针对视频文件和字幕文件。注意: 第2操作和下面（第3操作+第7操作）互斥，只能执行第2操作或（第3操作+第7操作），归类影片是针对“文件”还是“文件夹”。
                try:
                    jav, num_temp = classify_files(jav, num_fail, settings, dict_data, list_classify_basis,
                                                   dir_classify_target)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

                # 3重命名文件夹【相同】如果是针对“文件”归类，这一步会被跳过。 因为用户只需要归类视频文件，不需要管文件夹。
                try:
                    jav, num_temp = rename_folder(jav, num_fail, bool_rename_folder, dict_data, list_name_folder,
                                                  bool_separate_folder, num_all_episodes)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

                # 更新一下path_relative
                path_relative = f'{sep}{jav.path.replace(dir_choose, "")}'  # 影片的相对于所选文件夹的路径，用于报错

                # 4写入nfo【独特】
                if settings.bool_nfo:
                    # 如果是为空地准备的nfo，不需要多cd
                    if settings.bool_cd_only:
                        path_nfo = f'{jav.dir_current}{sep}{jav.name_no_ext.replace(str_cd, "")}.nfo'
                    else:
                        path_nfo = f'{jav.dir_current}{sep}{jav.name_no_ext}.nfo'
                    # nfo中tilte的写法
                    title_in_nfo = ''
                    for i in list_name_nfo_title:
                        title_in_nfo = f'{title_in_nfo}{dict_data[i]}'  # nfo中tilte的写法
                    # 开始写入nfo，这nfo格式是参考的kodi的nfo
                    f = open(path_nfo, 'w', encoding="utf-8")
                    f.write(f'<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n'
                            f'<movie>\n'
                            f'  <plot>{plot}</plot>\n'
                            f'  <title>{title_in_nfo}</title>\n'
                            f'  <originaltitle>{title}</originaltitle>\n'
                            f'  <rating>{score}</rating>\n'
                            f'  <criticrating>{criticrating}</criticrating>\n'
                            f'  <year>{dict_data["发行年份"]}</year>\n'
                            f'  <mpaa>NC-17</mpaa>\n'
                            f'  <customrating>NC-17</customrating>\n'
                            f'  <countrycode>JP</countrycode>\n'
                            f'  <premiered>{time_premiered}</premiered>\n'
                            f'  <release>{time_premiered}</release>\n'
                            f'  <runtime>{dict_data["片长"]}</runtime>\n'
                            f'  <country>日本</country>\n'
                            f'  <studio>{studio}</studio>\n'
                            f'  <id>{car}</id>\n"'
                            f'  <num>{car}</num>\n')
                    # 需要将特征写入genre
                    if settings.bool_genre:
                        for i in genres:
                            f.write(f'  <genre>{i}</genre>\n')
                        if settings.bool_write_studio and studio:
                            f.write(f'  <genre>片商:{studio}</genre>\n')
                        if list_extra_genres:
                            for i in list_extra_genres:
                                f.write(f'  <genre>{dict_data[i]}</genre>\n')
                    # 需要将特征写入tag
                    if settings.bool_tag:
                        for i in genres:
                            f.write(f'  <tag>{i}</tag>\n')
                        if settings.bool_write_studio and studio:
                            f.write(f'  <tag>片商:{studio}</tag>\n')
                        if list_extra_genres:
                            for i in list_extra_genres:
                                f.write(f'  <tag>{dict_data[i]}</tag>\n')
                    # 写入演员
                    f.write(f'  <actor>\n'
                            f'    <name>{dict_data["首个演员"]}</name>\n'
                            f'    <type>Actor</type>\n'
                            f'  </actor>\n')
                    f.write('</movie>\n')
                    f.close()
                    print('    >nfo收集完成')

                # 5需要两张封面图片【独特】
                if settings.bool_jpg:
                    # 下载海报的地址 cover
                    # fanart和poster路径
                    path_fanart = f'{jav.dir_current}{sep}'
                    path_poster = f'{jav.dir_current}{sep}'
                    for i in list_name_fanart:
                        path_fanart = f'{path_fanart}{dict_data[i]}'
                    for i in list_name_poster:
                        path_poster = f'{path_poster}{dict_data[i]}'
                        # kodi只需要一份图片，图片路径唯一
                    if settings.bool_cd_only:
                        path_fanart = path_fanart.replace(str_cd, '')
                        path_poster = path_poster.replace(str_cd, '')
                    # emby需要多份，现在不是第一集，直接复制第一集的图片
                    elif jav.episode != 1:
                        try:
                            copyfile(path_fanart.replace(str_cd, '-cd1'), path_fanart)
                            print('    >fanart.jpg复制成功')
                            copyfile(path_poster.replace(str_cd, '-cd1'), path_poster)
                            print('    >poster.jpg复制成功')
                        except FileNotFoundError:
                            pass
                    # kodi或者emby需要的第一份图片
                    if check_picture(path_fanart):
                        # print('    >已有fanart.jpg')
                        pass
                    else:
                        # 下载封面
                        print('    >从jav321下载封面: ', url_cover)
                        try:
                            download_pic(url_cover, path_fanart, proxy_321)
                            print('    >fanart.jpg下载成功')
                        except:
                            num_fail += 1
                            record_fail(f'    >第{num_fail}个失败！下载fanart.jpg失败: {url_cover}，{path_relative}\n')
                            continue  # 退出对该jav的整理
                    # 下载海报
                    if check_picture(path_poster):
                        # print('    >已有poster.jpg')
                        pass
                    elif url_cover == url_poster:  # 有些素人片，没有fanart和poster之分，只有一张接近正方形的图片
                        # 裁剪生成 poster
                        crop_poster_default(path_fanart, path_poster, 2)
                        # 需要加上条纹
                        if settings.bool_watermark_subtitle and bool_subtitle:
                            add_watermark_subtitle(path_poster)
                        if settings.bool_watermark_divulge and bool_divulge:
                            add_watermark_divulge(path_poster)
                    else:
                        # 下载poster.jpg
                        print('    >从jav321下载poster: ', url_poster)
                        try:
                            download_pic(url_poster, path_poster, proxy_321)
                            print('    >poster.jpg下载成功')
                            # 需要加上条纹
                            if settings.bool_watermark_subtitle and bool_subtitle:
                                add_watermark_subtitle(path_poster)
                            if settings.bool_watermark_divulge and bool_divulge:
                                add_watermark_divulge(path_poster)
                        except:
                            num_fail += 1
                            record_fail(f'    >第{num_fail}个失败！poster下载失败: {url_poster}，{path_relative}\n')
                            continue

                # 6收集演员头像【相同】

                # 7归类影片，针对文件夹【相同】
                try:
                    num_temp = classify_folder(jav, num_fail, settings, dict_data, list_classify_basis, dir_classify_target,
                                               dir_current, bool_separate_folder, num_all_episodes)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

            except:
                num_fail += 1
                record_fail(f'    >第{num_fail}个失败！发生错误，如一直在该影片报错请截图并联系作者: {path_relative}\n{format_exc()}\n')
                continue  # 【退出对该jav的整理】

    # 完结撒花
    print('\n当前文件夹完成，', end='')
    if num_fail > 0:
        print('失败', num_fail, '个!  ', dir_choose, '\n')
        line = -1
        with open('【可删除】失败记录.txt', 'r', encoding="utf-8") as f:
            content = list(f)
        while 1:
            if content[line].startswith('已'):
                break
            line -= 1
        for i in range(line + 1, 0):
            print(content[i], end='')
        print('\n“【可删除】失败记录.txt”已记录错误\n')
    else:
        print(' “0”失败！  ', dir_choose, '\n')
    # os.system('pause')
    input_start_key = input('回车继续选择文件夹整理: ')
