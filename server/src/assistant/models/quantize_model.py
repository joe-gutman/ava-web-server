from transformers import AutoTokenizer, TextGenerationPipeline
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

def quantize_model(model_dir, bits, group_size):
    try:
        quantizing_start = time.time()
        if bits is None or group_size is None:
            raise Exception("Bits and group_size must be provided")
        
        quantize_config = BaseQuantizeConfig(bits=bits, group_size=group_size)
        model = AutoGPTQForCausalLM.from_pretrained(model_dir, quantize_config)
        tokenizer = AutoTokenizer.from_pretrained(model_dir)

        examples = [
            tokenizer(
                "auto-gptq is an easy-to-use model quantization library with user-friendly apis, based on GPTQ algorithm."
            )
        ]

        save_dir = model_dir + "-" + str(bits) + "bit-" + str(group_size) + "g"

        logging.debug(f"Quantizing model: {model_dir} with {bits} bits and group size: {group_size}")

        model.quantize(examples)

        model.save_quantized(save_dir)
        tokenizer.save_pretrained(save_dir)
        logging.debug(f"Model quantized in: {round(time.time() - quantizing_start)} seconds")
        logging.debug(f"Quantized model saved to: {save_dir}")
        return save_dir
    except Exception as e:
        logging.error(e)
        return None
    

model = "Wizard-Vicuna-13B-Uncensored-GPTQ"
bits = 4
group_size = 128
quantize_model(f".\{model_name}", bits, group_size) 