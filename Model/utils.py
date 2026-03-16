from transformers import  BitsAndBytesConfig

quant_configs = {
        "bit_4_quant_config" :    BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype="float16",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type = "nf4"
        ),
        "bit_8_quant_config" :    BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype="float16",
                bnb_8bit_use_double_quant=True,
                bnb_8bit_quant_type = "nf4"
        )
}
