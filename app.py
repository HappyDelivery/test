import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 설정 및 구성 (Configuration)
# ==========================================
st.set_page_config(
    page_title="나만의 AI 어시스턴트",
    page_icon="🤖",
    layout="wide"
)

# 사이드바에서 API 키 입력 받기 (보안을 위해)
# 실제 배포시에는 st.secrets를 사용하는 것이 좋습니다.
with st.sidebar:
    st.header("설정 (Settings)")
    api_key = st.text_input("Google API Key를 입력하세요", type="password")
    
    # AI Studio에 있던 'System Instruction'을 여기에 넣으세요
    system_instruction = st.text_area(
        "시스템 프롬프트 (System Instruction)",
        value="당신은 도움이 되는 AI 어시스턴트입니다. 명확하고 친절하게 답변하세요.",
        height=200
    )
    
    st.divider()
    model_type = st.selectbox("모델 선택", ["gemini-1.5-flash", "gemini-1.5-pro"])
    temperature = st.slider("창의성 (Temperature)", 0.0, 2.0, 1.0)

# ==========================================
# 2. 로직 구현 (Logic)
# ==========================================

# API 키가 없으면 경고 표시 후 중단
if not api_key:
    st.info("좌측 사이드바에 Google API Key를 입력해주세요.")
    st.stop()

# Gemini 설정
try:
    genai.configure(api_key=api_key)
    # 시스템 프롬프트가 적용된 모델 생성
    model = genai.GenerativeModel(
        model_name=model_type,
        system_instruction=system_instruction,
        generation_config={"temperature": temperature}
    )
except Exception as e:
    st.error(f"API 설정 중 오류가 발생했습니다: {e}")
    st.stop()

# 세션 상태 초기화 (대화 기록 저장용)
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 3. UI 렌더링 (UI Rendering)
# ==========================================

st.title("🚀 My AI App Service")
st.caption("Powered by Google Gemini & Streamlit")

# 기존 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 1. 사용자 메시지 표시 및 저장
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. AI 응답 생성 및 표시
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 대화 기록을 포함하여 문맥 유지 (Context Retention)
            # Gemini는 history 객체를 따로 관리하지만, Streamlit 방식에 맞춰 매번 history를 구성하거나
            # start_chat을 이용할 수 있습니다. 여기서는 1회성 턴 방식 예시이나,
            # 멀티턴(대화 기억)을 위해 chat session을 구성합니다.
            
            history = [
                {"role": m["role"], "parts": [m["content"]]} 
                for m in st.session_state.messages[:-1] # 현재 프롬프트 제외
            ]
            
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt, stream=True)
            
            # 스트리밍 효과 구현
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"에러 발생: {e}")
            full_response = "죄송합니다. 오류가 발생하여 답변할 수 없습니다."

    # 3. AI 응답 저장
    st.session_state.messages.append({"role": "model", "content": full_response})
