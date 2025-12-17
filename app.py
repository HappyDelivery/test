import streamlit as st
import google.generativeai as genai
import os

# 1. 화면 설정
st.set_page_config(page_title="AI 솔루션 가이드", page_icon="🤖")

st.title("🤖 AI 솔루션 가이드")

# [버전 확인용 코드] 화면에 현재 도구 버전을 출력합니다.
# 만약 이 숫자가 0.8.3보다 낮게 나오면 업데이트가 안 된 거예요!
st.caption(f"🔧 현재 도구 버전: {genai.__version__}") 

st.write("당신에게 딱 맞는 AI 도구를 찾아드리고, 활용법까지 알려드려요!")

# 2. 비밀 금고에서 여권(API Key) 꺼내기
my_api_key = os.environ.get("GOOGLE_API_KEY")

if not my_api_key:
    st.info("설정을 위해 잠시 기다려주세요... (API Key 준비 중)")
    st.stop()

# 3. AI 로봇 설정
genai.configure(api_key=my_api_key)

system_instruction = """
당신은 사용자의 요청에 맞춰 최적의 AI 도구를 추천해 주는 'AI 활용 전문가'입니다.
사용자가 텍스트를 입력하거나 파일을 업로드하면, 다음 순서와 형식에 맞춰 답변해주세요:
1. **추천 AI 도구:** (가장 적합한 도구 이름)
2. **가격 정책:** (무료 / 유료 / 부분 유료 등 명시)
3. **활용 방법 (Step-by-Step):** 초보자도 따라 할 수 있게 1, 2, 3 단계로 아주 쉽게 설명
4. **활용 예시:** 실제 적용해 볼 수 있는 구체적인 사례
**주의사항:** 설명은 친절하고 전문적인 톤을 유지하세요.
"""

# 다시 최신 모델(gemini-1.5-flash)로 변경!
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=system_instruction
)

# 4. 채팅창 만들기
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("어떤 AI가 필요하신가요? (예: 로고를 만들어주는 무료 AI 추천해줘)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("전문가가 답변을 작성 중입니다..."):
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"에러가 났어요: {e}")
