import streamlit as st
import google.generativeai as genai
import os

# 1. 화면 설정
st.set_page_config(page_title="AI 솔루션 가이드", page_icon="🤖")
st.title("🤖 AI 솔루션 가이드")

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

# 4. [지능형 모델 연결] 선생님 목록에 있는 '되는 놈'을 찾습니다!
@st.cache_resource
def get_model():
    # ★ 핵심 수정: 선생님 탐정 목록에 '실제로 있던 이름'들만 넣었습니다!
    candidates = [
        "gemini-2.0-flash-exp",   # 1순위: 성능 좋고 무료 쿼터가 넉넉한 실험 버전
        "gemini-flash-latest",    # 2순위: 최신 플래시 모델 별명
        "gemini-2.0-flash-lite-preview-02-05", # 3순위: 가벼운 최신 프리뷰
        "gemini-exp-1206"         # 4순위: 또 다른 실험 버전
    ]
    
    selected_model = None
    last_error = None

    for name in candidates:
        try:
            # 테스트 연결 시도
            test_model = genai.GenerativeModel(name)
            # 아주 간단한 인사로 생존 확인
            test_model.generate_content("Hi")
            selected_model = name
            break # 성공하면 반복문 탈출!
        except Exception as e:
            last_error = e
            continue # 실패하면 다음 모델 시도

    if selected_model:
        return genai.GenerativeModel(selected_model, system_instruction=system_instruction), selected_model, None
    else:
        return None, None, last_error

# 모델 불러오기
model, model_name, error_msg = get_model()

if model:
    st.caption(f"🚀 연결 성공! 현재 작동 모델: {model_name}")
else:
    # 어떤 에러인지 화면에 자세히 보여줍니다 (디버깅용)
    st.error(f"😭 연결 가능한 모델을 찾지 못했습니다.\n마지막 에러 내용: {error_msg}")
    st.stop()

# 5. 채팅창 만들기
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내용 보여주기
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자가 입력했을 때 처리
if prompt := st.chat_input("어떤 AI가 필요하신가요? (예: 로고를 만들어주는 무료 AI 추천해줘)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("전문가가 답변을 작성 중입니다..."):
            try:
                chat = model.start_chat(history=[]) 
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"답변 중 에러가 났어요: {e}")
