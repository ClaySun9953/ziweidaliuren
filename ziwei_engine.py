import math
from lunar_python import Lunar, Solar

class ZiWeiEngine:
    def __init__(self):
        self.ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        self.GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        self.ZIWEI_STARS = {0:"紫微", 1:"天机", 3:"太阳", 4:"武曲", 5:"天同", 8:"廉贞"}
        self.TIANFU_STARS = {0:"天府", 1:"太阴", 2:"贪狼", 3:"巨门", 4:"天相", 5:"天梁", 6:"七杀", 10:"破军"}

    def get_lunar_info(self, dt):
        solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        lunar = solar.getLunar()
        
        # 获取农历月份 (lunar-python 中，闰月返回负数，例如闰4月返回 -4)
        raw_month = lunar.getMonth()
        is_leap = (raw_month < 0)
        
        # ==========================================
        # 核心规则注入：激进派 (闰月作下月算)
        # ==========================================
        actual_month = abs(raw_month)
        if is_leap:
            actual_month += 1
            if actual_month > 12: 
                actual_month = 1 # 极小概率边界：闰腊月归一
        
        return {
            "lunar_month": actual_month, 
            "lunar_day": lunar.getDay(),     
            "year_gan": lunar.getYearGan(),  
            "hour_zhi_idx": ((dt.hour + 1) % 24) // 2,
            "is_leap_original": is_leap
        }

    def calc_palace_layout(self, lunar_month, hour_zhi_idx):
        # 寅宫起步(索引2)，顺数月，逆数时定命宫；顺数时定身宫
        ming_idx = (2 + (lunar_month - 1) - hour_zhi_idx) % 12
        shen_idx = (2 + (lunar_month - 1) + hour_zhi_idx) % 12
        return ming_idx, shen_idx

    def calc_wuxing_ju(self, year_gan, ming_idx):
        gan_idx = self.GAN.index(year_gan)
        # 五虎遁求命宫天干
        ming_gan_idx = ((gan_idx % 5) * 2 + 2 + ming_idx - 2) % 10
        
        # 六十甲子纳音五行局速算法
        g = ming_gan_idx // 2
        z = (ming_idx // 2) % 3
        ju_value = ((g + z) % 5) + 1
        ju_num = [2, 6, 3, 4, 5][ju_value - 1] # 2水, 6火, 3木, 4金, 5土
        
        ju_names = {2:"水二局", 3:"木三局", 4:"金四局", 5:"土五局", 6:"火六局"}
        return ju_num, ju_names[ju_num]

    def deploy_main_stars(self, lunar_day, ju_num):
        # 紫微星定位
        dividend = lunar_day
        remainder = dividend % ju_num
        add_factor = ju_num - remainder if remainder != 0 else 0
        quotient = (dividend + add_factor) // ju_num
        
        if add_factor % 2 != 0: ziwei_idx = (1 + quotient - add_factor) % 12
        else: ziwei_idx = (1 + quotient + add_factor) % 12
            
        # 天府星定位 (寅申线对称)
        tianfu_idx = (14 - ziwei_idx) % 12
        
        palaces = {i: [] for i in range(12)}
        for offset, star in self.ZIWEI_STARS.items(): palaces[(ziwei_idx - offset) % 12].append(star)
        for offset, star in self.TIANFU_STARS.items(): palaces[(tianfu_idx + offset) % 12].append(star)
            
        return ziwei_idx, tianfu_idx, palaces

    def run(self, dt):
        info = self.get_lunar_info(dt)
        ming, shen = self.calc_palace_layout(info["lunar_month"], info["hour_zhi_idx"])
        ju_num, ju_name = self.calc_wuxing_ju(info["year_gan"], ming)
        ziwei, tianfu, stars_layout = self.deploy_main_stars(info["lunar_day"], ju_num)
        
        # 将 12 宫数据格式化返回
        formatted_palaces = {}
        for i in range(12):
            p_name = self.ZHI[i]
            tags = []
            if i == ming: tags.append("【命宫】")
            if i == shen: tags.append("【身宫】")
            stars_str = " ".join(stars_layout[i]) if stars_layout[i] else "空宫"
            formatted_palaces[p_name] = f"{''.join(tags)} {stars_str}"
            
        return {
            "lunar_month": info["lunar_month"],
            "lunar_day": info["lunar_day"],
            "is_leap_corrected": info["is_leap_original"],
            "wuxing_ju": ju_name,
            "palaces": formatted_palaces
        }