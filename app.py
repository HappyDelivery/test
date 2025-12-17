import streamlit as st
import google.generativeai as genai
import os

st.title("🕵️ AI 모델 탐정")
st.write("현재 내 API 키로 사용할 수 있는 모델을 찾고 있어요...")

# 1. API 키 가져오기
my_api_key = os.environ.get("GOOGLE_API_KEY")

if not my_api_key:
    st.error("API 키가 설정되지 않았어요!")
    st.stop()

# 2. 구글 AI 연결
genai.configure(api_key=my_api_key)

# 3. 사용 가능한 모델 목록 조회 (핵심!)
try:
    models = []
    # 'generateContent' (대화하기) 기능이 있는 모델만 찾아요
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            models.append(m.name)

    if models:
        st.success(f"와! {len(models)}개의 모델을 발견했어요! 🎉")
        st.code("\n".join(models)) # 화면에 목록을 보여줍니다
        st.info("위 목록 중에서 맘에 드는 이름을 알려주세요.")
    else:
        st.error("API 키는 연결됐는데, 사용할 수 있는 모델이 하나도 없대요. 😭 (새 프로젝트라 시간이 좀 걸리거나, 키 권한 문제일 수 있어요)")

except Exception as e:
    st.error(f"오류가 났어요. API 키가 잘못되었거나 인터넷 문제일 수 있어요.\n에러 내용: {e}")
