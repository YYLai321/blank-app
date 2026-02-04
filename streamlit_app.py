import streamlit as st
import ezdxf
from sectionproperties.analysis import Section
from sectionproperties.pre.geometry import Geometry
import matplotlib.pyplot as plt
import tempfile
import os

# --- 設定網頁標題與版面 ---
st.set_page_config(page_title="鋁斷面強度計算機 (AA 2020)", layout="wide")

st.title("🏗️ 鋁擠型斷面性質計算機 (AA 2020)")
st.markdown("""
此工具依據 **AA 2020 鋁結構規範**，自動計算斷面的幾何性質與塑性模數 ($Z$)。
請上傳 **封閉聚合線 (Closed Polyline)** 的 DXF 檔案 (單位: mm)。
""")

# --- 側邊欄：設定與上傳 ---
with st.sidebar:
    st.header("1. 檔案上傳")
    uploaded_file = st.file_uploader("上傳 DXF 檔", type=["dxf"])
    
    st.header("2. 分析設定")
    mesh_size = st.slider("網格密度 (Mesh Size)", min_value=1.0, max_value=10.0, value=2.5, step=0.5, 
                          help="數值越小越精確，但計算時間越久。通常 2.5mm 適合大部分鋁擠型。")
    
    st.markdown("---")
    st.info("💡 **提示：**\nDXF 圖檔必須由「封閉聚合線」組成，不可有重疊線段或破口，否則無法生成網格。")

# --- 主程式邏輯 ---
if uploaded_file is not None:
    # Streamlit 上傳的是 Bytes，需轉存為暫存檔供 ezdxf 讀取
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        with st.spinner('正在進行有限元素網格劃分與積分計算...'):
            # 1. 讀取幾何
            geometry = Geometry.from_dxf(tmp_path)
            
            # 2. 建立網格
            geometry.create_mesh(mesh_sizes=[mesh_size])
            
            # 3. 建立斷面物件並計算
            sec = Section(geometry=geometry)
            sec.calculate_geometric_properties()
            sec.calculate_plastic_properties() # AA 2020 關鍵步驟
            
            # 4. 取得數據 (原始單位 mm)
            area = sec.get_area()
            ixx, iyy = sec.get_ic()
            
            # 彈性模數 S (取最小值)
            s_modes = sec.get_s()
            sxx = min(s_modes[0], s_modes[1]) # Top/Bottom 取小
            syy = min(s_modes[2], s_modes[3]) # Right/Left 取小
            
            # 塑性模數 Z
            zxx, zyy = sec.get_z()

            # --- 顯示結果 (轉換為 cm 單位) ---
            st.success("計算完成！")
            
            # 建立三欄位顯示核心數據
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("斷面積 (Area)", f"{area/100:.2f} cm²")
            
            with col2:
                st.subheader("強軸 (X-Axis)")
                st.metric("慣性矩 (Ixx)", f"{ixx/10000:.2f} cm⁴")
                st.metric("彈性模數 (Sxx)", f"{sxx/1000:.2f} cm³")
                st.metric("塑性模數 (Zxx)", f"{zxx/1000:.2f} cm³", delta="AA 2020")

            with col3:
                st.subheader("弱軸 (Y-Axis)")
                st.metric("慣性矩 (Iyy)", f"{iyy/10000:.2f} cm⁴")
                st.metric("彈性模數 (Syy)", f"{syy/1000:.2f} cm³")
                st.metric("塑性模數 (Zyy)", f"{zyy/1000:.2f} cm³", delta="AA 2020")

            st.markdown("---")

            # --- AA 2020 深度分析 ---
            st.subheader("📊 AA 2020 設計規範檢核")
            
            # 計算形狀係數
            shape_factor_x = zxx / sxx
            shape_factor_y = zyy / syy

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown(f"**強軸形狀係數 (Zx/Sx):** `{shape_factor_x:.2f}`")
                if shape_factor_x > 1.5:
                    st.warning("⚠️ 形狀係數 > 1.5。依據 AA 2020，強軸強度計算上限應取 `1.5 * My`。")
                else:
                    st.success(f"✅ 可完全利用塑性強度！比舊版規範提升約 **{(shape_factor_x-1)*100:.1f}%** 強度。")

            with col_b:
                st.markdown(f"**弱軸形狀係數 (Zy/Sy):** `{shape_factor_y:.2f}`")
                if shape_factor_y > 1.5:
                    st.warning("⚠️ 形狀係數 > 1.5。依據 AA 2020，弱軸強度計算上限應取 `1.5 * My`。")
                else:
                    st.success(f"✅ 可完全利用塑性強度！比舊版規範提升約 **{(shape_factor_y-1)*100:.1f}%** 強度。")

            # --- 繪圖區 ---
            st.markdown("---")
            st.subheader("📐 斷面網格與形心檢視")
            
            # 使用 matplotlib 繪圖並傳入 Streamlit
            fig, ax = plt.subplots(figsize=(10, 8))
            sec.plot_mesh(ax=ax, materials=False, alpha=0.5)
            # 標示形心
            cx, cy = sec.get_c()
            ax.plot(cx, cy, 'rx', markersize=10, label='Centroid (形心)')
            ax.legend()
            ax.set_aspect('equal')
            ax.set_title("Finite Element Mesh")
            st.pyplot(fig)

    except Exception as e:
        st.error(f"分析失敗：{e}")
        st.markdown("### 可能原因：")
        st.markdown("""
        1. **DXF 不是封閉區域**：請檢查 CAD 中的聚合線是否已閉合 (Closed)。
        2. **線條重疊**：請使用 `OVERKILL` 指令清理 CAD 圖檔。
        3. **單位問題**：DXF 預設應為 mm 單位。
        """)
    
    finally:
        # 清除暫存檔
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

else:
    st.info("👈 請從左側側邊欄上傳 DXF 檔案以開始分析")
