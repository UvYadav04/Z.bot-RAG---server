import os
import torch
from utils.safeExecution import safeExecution
from openai import OpenAI

# MODEL_PATH = "Model/local"
# modelNames={
#     "Qwen/Qwen2.5-7B-Instruct":{
#         "model_name" : "Qwen/Qwen2.5-7B-Instruct",
#         "local_path" : f"{MODEL_PATH}/Qwen7.5B-Instruct"
#     },
#     "Qwen/Qwen2.5-0.5B-Instruct":{
#         "model_name" : "Qwen/Qwen2.5-0.5B-Instruct",
#         "local_path" : f"{MODEL_PATH}/Qwen0.5B-Instruct"
#     }
# }

# env = os.getenv("ENV", "DEVELOPMENT")
# MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct" if  env == "DEVELOPMENT"  else  "Qwen/Qwen2.5-7B-Instruct"
# @safeExecution
# def load_model(model_name = MODEL_NAME, load_in=4):
#     print("Logging into Hugging Face Hub...")
#     # login()
#     # print("Loading model with quantization:", load_in, "bits")
#     if env == "DEVELOPMENT":
#         device = "cpu"
#         dtype = torch.float32
#     else:
#         device = "auto"
#         dtype = torch.float16
#     print(f"Using device: {device}, dtype: {dtype}")
#     # check if model exists locally
#     model_source = modelNames[model_name]['local_path'] if os.path.exists(f"{modelNames[model_name]['local_path']}/config.json") else model_name
#     # model_source = model_name
#     print("Model source:", model_source)
#     if load_in == 4:
#         quant_config = quant_configs["bit_4_quant_config"]
#         dtype = torch.float16
#     elif load_in == 8:
#         quant_config = quant_configs["bit_8_quant_config"]
#         dtype = torch.float16
#     else:
#         quant_config = None
#         dtype = torch.float16
#     print(model_source)
#     model = AutoModelForCausalLM.from_pretrained(
#         model_source,
#         device_map=device,
#         dtype=dtype
#     )
#     # print(model)
#     tokenizer = AutoTokenizer.from_pretrained(model_source)
#     # print(tokenizer)
#     # save locally if first download
#     if model_source == model_name:
#         os.makedirs(modelNames[model_name]['local_path'], exist_ok=True)
#         model.save_pretrained(modelNames[model_name]['local_path'])
#         tokenizer.save_pretrained(modelNames[model_name]['local_path'])
#     tokenizer.pad_token = tokenizer.eos_token
#     model.config.pad_token_id = tokenizer.eos_token_id
#     print("Loaded model:", model_name)
#     # print(tokenizer.chat_template)
#     return model, tokenizer
@safeExecution
def load_model():
    client = OpenAI(
        api_key=os.environ.get("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )
    return client

@safeExecution
def get_model():
    return load_model()
