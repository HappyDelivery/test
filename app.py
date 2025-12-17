import streamlit as st
import google.generativeai as genai
import os

# 1. 화면 설정
st.set_page_config(page_title="AI 솔루션 가이드", page_icon="🤖")

st.title("🤖 AI 솔루션 가이드")
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

model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=system_instruction
)

# 4. 채팅창 만들기
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내용 보여주기
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자가 입력했을 때 처리
if prompt := st.chat_input("어떤 AI가 필요하신가요? (예: 로고를 만들어주는 무료 AI 추천해줘)"):
    # 사용자 질문 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 답변 표시
    with st.chat_message("assistant"):
        with st.spinner("전문가가 답변을 작성 중입니다..."):
            try:
                # 대화 맥락을 유지하며 답변 생성
                chat = model.start_chat(history=[]) 
                response = model.generate_content(prompt)
                st.markdown(response.text)
                
                # 답변 저장
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"에러가 났어요: {e}")
