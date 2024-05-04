from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted
from ChatBot_Extract_Intent.llm_predict import predict_llm
import requests
from ChatBot_Extract_Intent.config_app.config import get_config

config_app = get_config()
openai_api_key=config_app["parameter"]["openai_api_key"]

class ExtractNameAction(Action):

    def name(self) -> Text:
        return "action_extract_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_name = None

        for ent in tracker.latest_message.get("entities", []):
            if ent["entity"] == "user_name":
                user_name = ent["value"]

        # You can now use this name in your bot logic
        if user_name:
            dispatcher.utter_message(text=f"Xin chào {user_name}!\nRất vui được gặp {user_name}.Bạn có câu hỏi hoặc yêu cầu cụ thể nào liên quan đến dịch vụ mua sắm của VCC không? Tôi sẽ cố gắng giúp bạn một cách tốt nhất.!")
        else:
            dispatcher.utter_message(text="Xin chào! Tôi là BotV, trợ lý mua sắm của bạn. Tôi có thể giúp gì cho bạn hôm nay?.")

        return []

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],) -> List[Dict[Text, Any]]:

        # Lấy tin nhắn từ người dùng từ Rasa tracker
        user_message = tracker.latest_message.get("text")

        # Định nghĩa URL và các header cho yêu cầu đến API ChatGPT
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json",
        }

        # Định nghĩa dữ liệu cho yêu cầu đến API ChatGPT
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ]
        }
        
        # Gửi yêu cầu đến API ChatGPT
        response = requests.post(url, headers=headers, json=data)
        print(response)
        # Xử lý phản hồi từ API ChatGPT
        if response.status_code == 200:
            chatgpt_response = response.json()
            message = chatgpt_response["choices"][0]["message"]["content"]
            dispatcher.utter_message(message)
        else:
            # Xử lý lỗi nếu có
            dispatcher.utter_message("Xin lỗi, tôi không thể tạo phản hồi vào thời điểm này. Vui lòng thử lại sau.")

            # Revert lại tin nhắn từ người dùng dẫn đến fallback
            return [UserUtteranceReverted()]
        
# class productAPI(object):

#     def __init__(self) -> None:
#         self.db =
    
class Actionseachproduct(Action):
    def name(self) -> Text:
        return "action_search_product"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any], ) -> List[Dict[Text, Any]]:
        # Lấy tin nhắn từ người dùng từ Rasa tracker
        user_message = tracker.latest_message.get("text")

        # Call the llm_predict function and retrieve its result
        message = predict_llm(user_message, 'a', 'b', 'c', ' ')

        # You can now use the result as needed
        # print(f"Result from predict_llm: {result}")
        dispatcher.utter_message(message)
        # Return an empty list, as this is a custom action
        return []

