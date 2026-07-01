import streamlit as st
import datetime
import math
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 升级：NOAA (美国国家海洋和大气管理局) 高精度太阳均时差算法
# ---------------------------------------------------------
def get_equation_of_time(dt):
    # 提取一年中的第几天 (0-365)
    d = dt.timetuple().tm_yday - 1 
    # 换算当前时间为小数
    h = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    
    # γ (Gamma): 将当前时间映射到 2π 周期内的弧度 (精准包含闰年周期 365.24)
    gamma = (2 * math.pi / 365.24) * (d + (h - 12) / 24.0)
    
    # 高精度傅里叶级数展开 (天文级精度，误差缩小至极少数秒内)
    eot = 229.18 * (
        0.000075 
        + 0.001868 * math.cos(gamma) 
        - 0.032077 * math.sin(gamma) 
        - 0.014615 * math.cos(2 * gamma) 
        - 0.040849 * math.sin(2 * gamma)
    )
    return eot

# ==========================================
# 全球城市时空数据库 (经度, 时区, 时区标准子午线)
# ==========================================
CITY_DB = {
    "北京": {"lon": 116.40, "tz": "Asia/Shanghai", "meridian": 120.0},
    "哈尔滨": {"lon": 126.63, "tz": "Asia/Shanghai", "meridian": 120.0},
    "深圳": {"lon": 114.05, "tz": "Asia/Shanghai", "meridian": 120.0},
    "成都": {"lon": 104.06, "tz": "Asia/Shanghai", "meridian": 120.0},
    "纽约": {"lon": -74.00, "tz": "America/New_York", "meridian": -75.0},
    "洛杉矶": {"lon": -118.24, "tz": "America/Los_Angeles", "meridian": -120.0},
    "伦敦": {"lon": -0.12, "tz": "Europe/London", "meridian": 0.0},
    "东京": {"lon": 139.69, "tz": "Asia/Tokyo", "meridian": 135.0},
    "悉尼": {"lon": 151.20, "tz": "Australia/Sydney", "meridian": 150.0}
}
import random
# ==========================================
# 跨文件模块导入 (工程化核心)
# ==========================================
from core_engine import PrecisionSolarEngine, TimeAndGeo, QimenEngine, LiuYaoEngine
from ziwei_engine import ZiWeiEngine
from liuren_engine import DaLiuRenEngine

st.set_page_config(page_title="赛博玄学 V33.0 | 模块化矩阵版", layout="wide", page_icon="🧿")

# UI CSS 样式注入
st.markdown("""
<style>
    .card { background-color: #0E1117; border: 1px solid #414141; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; min-height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .card-kongwang { border: 2px solid #FF4B4B !important; box-shadow: 0 0 10px rgba(255, 75, 75, 0.2); }
    .card-header { font-size: 13px; color: #888; margin-bottom: 2px; }
    .card-god { font-size: 15px; color: #FF4B4B; font-weight: bold; }
    .card-star { font-size: 15px; color: #FFA500; }
    .card-door { font-size: 16px; color: #00CC96; font-weight: bold; margin: 3px 0; }
    .card-stem { font-size: 15px; color: #DDD; font-family: monospace; }
    .status-bar { padding: 10px; border-radius: 5px; background-color: #111; color: #00FF00; font-family: 'Courier New', monospace; margin-bottom: 20px; border: 1px dashed #333; }
    .gua-line { font-size: 26px; font-family: 'Courier New', monospace; font-weight: bold; margin: 5px 0; letter-spacing: 1px; }
    .gua-text-red { color: #FF4B4B; }
    .gua-text-normal { color: #E0E0E0; }
    .lr-table { width: 100%; text-align: center; font-size: 16px; margin-top: 10px; border-collapse: collapse; }
    .lr-table th, .lr-table td { border: 1px solid #444; padding: 8px; }
    .lr-table th { background-color: #222; color: #FFA500; }
</style>
""", unsafe_allow_html=True)

st.title("🧿 赛博玄学 V33.0 (模块化架构版)")

# ==========================================
# UI 控制流与状态管理
# ==========================================
if 'yao_list' not in st.session_state: st.session_state['yao_list'] = []
if 'u_info' not in st.session_state: st.session_state['u_info'] = {}

# ---------------------------------------------------------
# 新增：带内存缓存的地理编码器（只要查询词不变，瞬间返回结果）
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_cached_location(query):
    geolocator = Nominatim(user_agent="cyber_metaphysics_v33")
    try:
        loc = geolocator.geocode(query)
        if loc:
            return {
                "lon": loc.longitude, 
                "lat": loc.latitude, 
                "city_name": loc.address.split(',')[0],
                "address": loc.address
            }
    except Exception:
        return None
    return None

with st.sidebar:
    st.header("🔮 本地定场录入")
    
    # 增加了一个智能搜索模式
    loc_mode = st.radio("定位模式", ["📍 快速选城", "🔍 智能搜索 (全自动)", "🎯 精确坐标 (手动)"], horizontal=False)
    
    # 初始化默认值
    city_name = "未知坐标"
    lon = 126.63
    lat = 45.75
    
    if loc_mode == "📍 快速选城":
        CITY_DB = {
            "北京": {"lon": 116.40, "lat": 39.90},
            "哈尔滨": {"lon": 126.63, "lat": 45.75},
            "深圳": {"lon": 114.05, "lat": 22.52},
            "成都": {"lon": 104.06, "lat": 30.67},
        }
        selected_city = st.selectbox("选择城市", list(CITY_DB.keys()))
        city_name = selected_city
        lon = CITY_DB[selected_city]["lon"]
        lat = CITY_DB[selected_city]["lat"]
        
    elif loc_mode == "🔍 智能搜索 (全自动)":
        search_query = st.text_input("🌍 输入地名 (如: 漠河 / 纽约曼哈顿)", value="哈尔滨")
        if search_query:
            with st.spinner('📡 正在读取时空坐标...'):
                # 调用缓存函数，避免重复请求
                loc_data = get_cached_location(search_query)
            
            if loc_data:
                lon = loc_data["lon"]
                lat = loc_data["lat"]
                city_name = loc_data["city_name"]
                st.success(f"锁定坐标: {city_name} (经度 {lon:.4f})")
                st.caption(f"完整地址: {loc_data['address']}")
            else:
                st.error("❌ 未能解析该地点，请尝试输入更大的行政区划。")
            
                
    else:
        st.caption("请查阅手机指南针或地图软件")
        lon = st.number_input("经度 (Longitude)", value=126.6300, format="%.4f")
        lat = st.number_input("纬度 (Latitude)", value=45.7500, format="%.4f")
        city_name = f"手动经度:{lon:.2f}"

    # ==========================================
    # 以下是不变的时区计算和 Form 提交逻辑
    # ==========================================
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat) 
    
    if tz_name:
        tz = pytz.timezone(tz_name)
        local_now = datetime.now(tz)
        utc_offset_hours = local_now.utcoffset().total_seconds() / 3600
        meridian = utc_offset_hours * 15.0
    else:
        tz = pytz.timezone("UTC")
        local_now = datetime.utcnow()
        meridian = 0.0
        st.warning("⚠️ 坐标处于无人区或海洋，已回退至 UTC 零时区。")

    with st.form("entry_form"):
        u_date = st.date_input("🗓️ 日期", local_now.date())
        u_time = st.time_input("⏰ 时间", local_now.time())
        name = st.text_input("👤 求测人")
        ask = st.text_input("🖊️ 问事")
        
        if st.form_submit_button("🔵 锁定本地时空", type="primary") and name and ask:
            st.session_state['u_info'] = {
                "city": city_name, 
                "name": name, 
                "ask": ask, 
                "dt": datetime.combine(u_date, u_time),
                "lon": lon,
                "meridian": meridian
            }
            st.session_state['yao_list'] = []
            st.rerun()


if not st.session_state['u_info']:
    st.info("👈 请在侧边栏手动设定时空锚点开启排盘。")
else:
    info = st.session_state['u_info']
    count = len(st.session_state['yao_list'])
    
    if count < 6:
        st.subheader(f"🪙 起卦仪式：请摇第 {count + 1} 爻")
        st.write("当前卦象 (初爻在下):")
        for i in range(count - 1, -1, -1):
            val = st.session_state['yao_list'][i]
            if val == 6: st.markdown("<div class='gua-line gua-text-red'>■■ ■■ &nbsp;&nbsp;(老阴)</div>", unsafe_allow_html=True)
            elif val == 7: st.markdown("<div class='gua-line gua-text-normal'>■■■■■ &nbsp;&nbsp;(少阳)</div>", unsafe_allow_html=True)
            elif val == 8: st.markdown("<div class='gua-line gua-text-normal'>■■ ■■ &nbsp;&nbsp;(少阴)</div>", unsafe_allow_html=True)
            elif val == 9: st.markdown("<div class='gua-line gua-text-red'>■■■■■ &nbsp;&nbsp;(老阳)</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🎲 点击摇出此爻", use_container_width=True, type="primary"):
            st.session_state['yao_list'].append(random.choice([6, 7, 7, 7, 8, 8, 8, 9]))
            st.rerun()
            
    else:
        st.success("时空锁定，四大引擎并发解算完成。")
        
        # ==========================================
        # 1. 初始化时空参数 (经度修正 + 天文均时差修正)
        # ==========================================
        lon = info.get('lon', 120.0)
        meridian = info.get('meridian', 120.0)
        
        # A. 经度带来的平太阳差值 (分钟)
        m_diff = (lon - meridian) * 4 
        
        # B. 地球公转轨道带来的均时差 (分钟)
        eot_diff = get_equation_of_time(info['dt'])
        
        # C. 终极推导：真太阳时 = 钟表时间 + 经度差 + 均时差
        total_minutes_diff = m_diff + eot_diff
        t_solar = info['dt'] + timedelta(minutes=total_minutes_diff)
        
        # se = PrecisionSolarEngine() ... (后面接原代码)
        
               
        # 2. 调用核心引擎 (core_engine.py)
        se = PrecisionSolarEngine()
        slong, term, dun_type, ju_map, yue_jiang = se.get_solar_data(t_solar)
        
        tg = TimeAndGeo()
        p = tg.get_pillars(t_solar)
       # 先用节气名(term)拿到上中下三元的数组，再用元局索引(yuan_idx)取具体数字
        ju = ju_map[term][p['yuan_idx']]
        qm = QimenEngine()
        q_layout, q_star, q_door = qm.run(ju, dun_type=="阳遁", p['xun'], p['h_gan'], p['h_zhi'], p['kw'])
        
        ly = LiuYaoEngine()
        g_data = ly.process(st.session_state['yao_list'])
        
        # 3. 调用紫微引擎 (ziwei_engine.py)
        zw = ZiWeiEngine()
        z_data = zw.run(t_solar)
        
        # 4. 调用大六壬引擎 (liuren_engine.py)
        lr = DaLiuRenEngine()
        r_data = lr.run(yue_jiang, p['h_zhi'], p['day_gan'], p['day_zhi'])

        # ==========================================
        # 渲染层：将运算结果吐给前端展示
        # ==========================================
        st.markdown(f"""
        <div class="status-bar">
        [时空总线] 太阳黄经: {slong:.4f}° | 经度: {lon}° | 平太阳修正: {m_diff:+.2f}m
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("真太阳时", t_solar.strftime('%m-%d %H:%M:%S'), "早子时" if p['is_early_zi'] else None)
        c2.metric("四柱", f"{p['year']} {p['month']} {p['day']} {p['hour']}")
        c3.metric("奇门定局", f"{term} {dun_type}{ju}局", p['kw']+"空")
        c4.metric("六壬月将", f"{yue_jiang}将", f"日干寄宫:{p['day_gan']}->{r_data['ji_gong']}")
        
        st.write(f"### 问测：{info['ask']}")
        st.divider()
        
        # 第一排：六爻与奇门
        col_left, col_right = st.columns([1, 2])
        with col_left:
            st.subheader("☯️ 六爻")
            st.write(f"**{g_data['ben']}** 变 **{g_data['bian']}**")
            for i in range(5, -1, -1):
                val = st.session_state['yao_list'][i]
                line = "━━━" if val in [7,9] else "━ ━"
                c = "#FF4B4B" if val in [6, 9] else "#E0E0E0"
                s = " O" if val == 9 else (" X" if val == 6 else "")
                st.markdown(f"<div style='font-size:22px; color:{c}; font-weight:bold; margin:2px 0;'>{line}{s}</div>", unsafe_allow_html=True)
            if g_data['moves']: st.warning(f"动爻: {g_data['moves']}")
        col_z, col_r = st.columns([2, 1])  
        with col_r:
            st.subheader("📜 大六壬 (三传四课)")
            sk = r_data['sike']
            sc = r_data['san_chuan']
            tp = r_data['tian_pan']
            jp = r_data['jiang_pan']
            
            st.caption(f"月将: **{yue_jiang}将** | 发用门类: **{r_data['san_chuan_rule']}**")
            
            # 三传渲染
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; text-align:center; margin-bottom:15px; background:#1E1E1E; padding:10px; border-radius:5px;">
                <div><div style="color:#888; font-size:12px;">初传</div><div style="color:#FF4B4B; font-weight:bold;">{sc[0]['jiang']}<br>{sc[0]['zhi']}</div></div>
                <div><div style="color:#888; font-size:12px;">中传</div><div style="color:#FFA500; font-weight:bold;">{sc[1]['jiang']}<br>{sc[1]['zhi']}</div></div>
                <div><div style="color:#888; font-size:12px;">末传</div><div style="color:#00CC96; font-weight:bold;">{sc[2]['jiang']}<br>{sc[2]['zhi']}</div></div>
            </div>
            """, unsafe_allow_html=True)
            
            # 四课渲染
            st.markdown(f"""
            <table class="lr-table">
                <tr><th>四课</th><th>三课</th><th>二课</th><th>一课</th></tr>
                <tr><td>{sk[0]['top']}</td><td>{sk[1]['top']}</td><td>{sk[2]['top']}</td><td>{sk[3]['top']}</td></tr>
                <tr><td>{sk[0]['bottom']}</td><td>{sk[1]['bottom']}</td><td>{sk[2]['bottom']}</td><td>{sk[3]['bottom']}</td></tr>
            </table>
            <br>
            <table class="lr-table" style="font-size:14px;">
                <tr><th colspan="6">天地盘与十二神将 (外将内神)</th></tr>
                <tr>
                    <td style="color:#888">巽</td>
                    <td>{jp['巳']}<br><b style="color:#00CC96">{tp['巳']}</b></td>
                    <td>{jp['午']}<br><b style="color:#00CC96">{tp['午']}</b></td>
                    <td>{jp['未']}<br><b style="color:#00CC96">{tp['未']}</b></td>
                    <td>{jp['申']}<br><b style="color:#00CC96">{tp['申']}</b></td>
                    <td style="color:#888">坤</td>
                </tr>
                <tr>
                    <td>{jp['辰']}<br><b style="color:#00CC96">{tp['辰']}</b></td><td colspan="4" rowspan="2" style="background:#111; color:#555;">地盘不动<br>天盘/神将游行</td><td>{jp['酉']}<br><b style="color:#00CC96">{tp['酉']}</b></td>
                </tr>
                <tr>
                    <td>{jp['卯']}<br><b style="color:#00CC96">{tp['卯']}</b></td><td>{jp['戌']}<br><b style="color:#00CC96">{tp['戌']}</b></td>
                </tr>
                <tr>
                    <td style="color:#888">艮</td>
                    <td>{jp['寅']}<br><b style="color:#00CC96">{tp['寅']}</b></td>
                    <td>{jp['丑']}<br><b style="color:#00CC96">{tp['丑']}</b></td>
                    <td>{jp['子']}<br><b style="color:#00CC96">{tp['子']}</b></td>
                    <td>{jp['亥']}<br><b style="color:#00CC96">{tp['亥']}</b></td>
                    <td style="color:#888">乾</td>
                </tr>
            </table>
            """, unsafe_allow_html=True)
        
        # 第二排：紫微与大六壬
        col_z, col_r = st.columns([2, 1])
        with col_z:
            st.subheader("🌌 紫微斗数")
            st.caption(f"农历 {z_data['lunar_month']}月 {z_data['lunar_day']}日 | **{z_data['wuxing_ju']}** {'(闰月降维)' if z_data['is_leap_corrected'] else ''}")
            zp = z_data['palaces']
            z1 = st.columns(4); z1[0].info(f"巳\n{zp['巳']}"); z1[1].info(f"午\n{zp['午']}"); z1[2].info(f"未\n{zp['未']}"); z1[3].info(f"申\n{zp['申']}")
            z2 = st.columns(4); z2[0].info(f"辰\n{zp['辰']}"); z2[3].info(f"酉\n{zp['酉']}")
            z3 = st.columns(4); z3[0].info(f"卯\n{zp['卯']}"); z3[3].info(f"戌\n{zp['戌']}")
            z4 = st.columns(4); z4[0].info(f"寅\n{zp['寅']}"); z4[1].info(f"丑\n{zp['丑']}"); z4[2].info(f"子\n{zp['子']}"); z4[3].info(f"亥\n{zp['亥']}")
            
        with col_r:
            st.subheader("📜 大六壬")
            sk = r_data['sike']
            st.markdown(f"""
            <table class="lr-table">
                <tr><th>四课</th><th>三课</th><th>二课</th><th>一课</th></tr>
                <tr><td>{sk[0]['top']}</td><td>{sk[1]['top']}</td><td>{sk[2]['top']}</td><td>{sk[3]['top']}</td></tr>
                <tr><td>{sk[0]['bottom']}</td><td>{sk[1]['bottom']}</td><td>{sk[2]['bottom']}</td><td>{sk[3]['bottom']}</td></tr>
            </table>
            <br>
            <table class="lr-table">
                <tr><th colspan="6">天地盘 (月将: {yue_jiang})</th></tr>
                <tr><td>天</td><td>{r_data['tian_pan']['巳']}</td><td>{r_data['tian_pan']['午']}</td><td>{r_data['tian_pan']['未']}</td><td>{r_data['tian_pan']['申']}</td><td>天</td></tr>
                <tr><td>辰</td><td></td><td></td><td></td><td></td><td>酉</td></tr>
                <tr><td>卯</td><td></td><td></td><td></td><td></td><td>戌</td></tr>
                <tr><td>地</td><td>{r_data['tian_pan']['寅']}</td><td>{r_data['tian_pan']['丑']}</td><td>{r_data['tian_pan']['子']}</td><td>{r_data['tian_pan']['亥']}</td><td>地</td></tr>
            </table>
            """, unsafe_allow_html=True)

        st.divider()
        
        # ==========================================
        # AI 综合断卦 Prompt 组装区
        # ==========================================
        
        # 1. 组装六爻文本 (构造字符画)
        gua_lines_txt = "--------------------------------------------------\n"
        for i in range(5, -1, -1):
            val = st.session_state['yao_list'][i]
            line_char = "-------" if val in [7,9] else "-     -"
            change_note = " [X]老阴" if val == 6 else (" [O]老阳" if val == 9 else (f" ({val})"))
            gua_lines_txt += f"  第{i+1}爻: {line_char} {change_note}\n"
        gua_lines_txt += "--------------------------------------------------"

        # 2. 组装奇门文本
        qm_txt = ""
        for i in range(1, 10):
            d = q_layout[i]
            if i == 5:
                qm_txt += f"宫5(中宫): {d.get('star','')} {d.get('god','')} {d.get('door','')} [地:{d.get('di','')}]\n"
            else:
                qm_txt += f"宫{i}: {d.get('star','')} {d.get('god','')} {d.get('door','')} [天:{d.get('tian','')}/地:{d.get('di','')}]\n"

        # 3. 组装紫微文本 (提取有星曜的宫位)
        zw_txt = " | ".join([f"{k}:{v.replace(' ','')}" for k,v in z_data['palaces'].items() if "空宫" not in v])

        # 4. 组装六壬文本
        sk = r_data['sike']
        lr_sike_txt = f"四课: 1课({sk[3]['top']}/{sk[3]['bottom']}) 2课({sk[2]['top']}/{sk[2]['bottom']}) 3课({sk[1]['top']}/{sk[1]['bottom']}) 4课({sk[0]['top']}/{sk[0]['bottom']})"
        tp = r_data['tian_pan']
        lr_tp_txt = "天地盘: " + " ".join([f"{di}乘{tian}" for di, tian in tp.items()])

        # 5. 拼装发给 AI 的终极指令
        raw_data = f"""
【问测】 {info['ask']}
【定场】 {info['name']} @ {info['city']} (经度:{lon:.4f}°，时空已校准)
【时间】 {t_solar.strftime('%Y-%m-%d %H:%M:%S')} (真太阳时 | 总修正:{m_diff:+.2f}分钟)
【四柱】 {p['year']} {p['month']} {p['day']} {p['hour']} (旬首:{p['xun']})

【六爻】 本卦：{g_data['ben']} | 变卦：{g_data['bian']} | 动爻：{g_data['moves']}
{gua_lines_txt}

【奇门】 {term} {dun_type}{ju}局 | 空亡:{p['kw']} | 值符:{q_star} | 值使:{q_door}
布局简析(宫1坎→宫9离)：
{qm_txt}
【紫微】 农历 {z_data['lunar_month']}月 {z_data['lunar_day']}日 | {z_data['wuxing_ju']}
排盘简析：{zw_txt}

【六壬】 月将：{yue_jiang} | 日干寄宫：{r_data['ji_gong']}
{lr_sike_txt}
{lr_tp_txt}

【AI 综合断卦与排盘解析指令】
请作为一位精通国学的易学大师，结合以上四大玄学体系的数据，为我解答【{info['ask']}】这件事情：
1. 【核心定局-六爻】：请首先列出《易经》中关于本卦（{g_data['ben']}）与变卦（{g_data['bian']}）的原版【卦辞】，并重点输出动爻（{g_data['moves']}）的原版【爻辞】。请通俗翻译这些辞文，以六爻定下整件事的吉凶大基调。
2. 【时空环境-奇门】：结合奇门九宫中值符、值使的落宫，以及用神落宫的星门神仪吉凶，分析当前面临的外部环境与时机。
3. 【先天定数-紫微】：参考紫微斗数命宫、身宫的主星相性，简批当事人面对此事的行为模式或运势状态。
4. 【事物演变-六壬】：通过大六壬四课的上下克贼关系（如上克下或下贼上），分析事情的内部矛盾与发展过程。
5. 【综合结论】：整合四家之言，给出清晰的成败判断、关键时间节点（应期推算）以及切实可行的策略建议。语气需详实客观。
"""
        st.text_area("复制以下全盘数据与指令，发送给大语言模型 (AI) 进行深度断卦：", raw_data, height=450)

        st.divider()
        if st.button("🔥 销毁所有存储并重置", type="primary"):
            st.session_state.clear()
            st.rerun()
