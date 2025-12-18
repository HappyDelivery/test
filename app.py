import streamlit as st
import google.generativeai as genai
import time

# --------------------------------------------------------------------------
# 1. 설정 및 구성 (Configuration)
# --------------------------------------------------------------------------

# 페이지 기본 설정
st.set_page_config(
    page_title="Happy Delivery AI",
    page_icon="🚚",
    layout="centered"
)

# [보안 주의] 실제 배포 시에는 이 키를 st.secrets에 저장해서 불러와야 합니다.
# 현재는 테스트를 위해 직접 입력해 두었습니다.
API_KEY = "AIzaSyBVxYQzLTs8uRP4yyJYS8yBDewLSm896Jg"

# --------------------------------------------------------------------------
# [중요] AI Studio의 'System Instructions' 내용을 아래 따옴표 안에 붙여넣으세요.
# 예: "너는 친절한 배달 상담원이야. 고객의 주문 상태를 확인해줘..."
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
당신은 최고의 AI 어시스턴트입니다. 
사용자의 질문에 친절하고 정확하게 답변하며, 이모지를 적절히 사용하여 생동감 있게 대화하세요.
(이곳에 Google AI Studio에서 작성했던 프롬프트 내용을 덮어쓰기 하세요)
"""

# 모델 설정 (가장 가성비 좋고 빠른 모델 선택)
MODEL_NAME = "gemini-1.5-flash" 

# --------------------------------------------------------------------------
# 2. 로직 구현 (Backend Logic)
# --------------------------------------------------------------------------

def configure_genai():
    try:
        genai.configure(api_key=API_KEY)
        # 시스템 프롬프트가 적용된 모델 생성
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT
        )
        return model
    except Exception as e:
        st.error(f"API 연결 오류: {e}")
        return None

# 세션 상태 초기화 (대화 기록 저장소)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 모델 초기화
model = configure_genai()

# --------------------------------------------------------------------------
# 3. 화면 구현 (Frontend UI)
# --------------------------------------------------------------------------

st.title("🚚 Happy Delivery AI Service")
st.markdown("---")

# 기존 대화 기록 표시 (채팅창 유지)
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("무엇을 도와드릴까요?"):
    
    # 1. 사용자 메시지 화면 표시
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. 대화 기록에 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. AI 응답 생성
    if model:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # 문맥(Context) 유지를 위해 과거 대화 내용을 모델에 전달
                # Gemini API 형식에 맞게 변환
                history_for_api = []
                for msg in st.session_state.messages[:-1]: # 현재 질문 제외하고 과거 기록만
                    role = "user" if msg["role"] == "user" else "model"
                    history_for_api.append({"role": role, "parts": [msg["content"]]})
                
                chat = model.start_chat(history=history_for_api)
                response = chat.send_message(prompt, stream=True)
                
                # 타자 치는 효과(Streaming) 구현
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        message_placeholder.markdown(full_response + "▌")
                        
                message_placeholder.markdown(full_response)
                
                # 4. AI 응답 기록 저장
                st.session_state.messages.append({"role": "model", "content": full_response})
                
            except Exception as e:
                error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "model", "content": error_msg})

# 사이드바 (추가 기능)
with st.sidebar:
    st.header("설정")
    if st.button("대화 내용 초기화 🗑️"):
        st.session_state.messages = []
        st.rerun()
    st.caption(f"Model: {MODEL_NAME}")
    st.caption("Powered by Google Gemini")
