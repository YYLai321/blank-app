import streamlit as st
import pandas as pd

# 設定頁面標題
st.set_page_config(page_title="玻璃強度與變形量檢核工具", layout="wide")

st.title("🏗️ 玻璃強度與變形量檢核系統")
st.write("請在左側輸入參數，右側將即時更新檢核結果。")

# --- 側邊欄：輸入參數 ---
st.sidebar.header("📋 輸入參數")

glass_type = st.sidebar.selectbox("玻璃種類", ["強化玻璃", "半強化玻璃", "一般浮法玻璃"])
width = st.sidebar.number_input("玻璃寬度 (mm)", value=1000)
height = st.sidebar.number_input("玻璃長度 (mm)", value=2000)
thickness = st.sidebar.number_input("玻璃公稱厚度 (mm)", value=10)
load = st.sidebar.number_input("設計荷載 (kPa / kN/m²)", value=2.0)

# --- 計算邏輯 (預留位置) ---
# 這裡會根據你稍後提供的表格公式進行修改
# 範例邏輯：
area = (width * height) / 1_000_000  # 面積 m2
max_stress = (load * area) / (thickness ** 2) * 500  # 模擬應力計算
max_deflection = (load * (width**4)) / (thickness**3 * 100000) # 模擬變形量計算

# 假設的門檻值
allowable_stress = 120 if glass_type == "強化玻璃" else 50
allowable_deflection = width / 60

# --- 右側：顯示結果 ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("計算應力 (N/mm²)", f"{max_stress:.2f}")
with col2:
    st.metric("計算變形量 (mm)", f"{max_deflection:.2f}")
with col3:
    status = "✅ 通過" if max_stress < allowable_stress else "❌ 不通過"
    st.metric("檢核狀態", status)

# --- 詳細數據表格 ---
st.divider()
st.subheader("📊 詳細分析數據")

data = {
    "項目": ["玻璃尺寸", "承受荷載", "計算應力", "許容應力", "變形量", "許容變形量"],
    "數值": [f"{width}x{height} mm", f"{load} kPa", f"{max_stress:.2f} MPa", f"{allowable_stress} MPa", f"{max_deflection:.2f} mm", f"{allowable_deflection:.2f} mm"],
    "結果": ["-", "-", "OK" if max_stress < allowable_stress else "NG", "-", "OK" if max_deflection < allowable_deflection else "NG", "-"]
}

df = pd.DataFrame(data)
st.table(df)

# 提供下載報表功能
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 下載檢核報表 (CSV)", csv, "glass_check.csv", "text/csv")
