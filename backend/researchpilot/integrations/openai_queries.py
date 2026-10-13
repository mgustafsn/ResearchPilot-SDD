"""Reserved adapter contract; no HTTP call is implemented yet."""


class OpenAIQueryProvider:
    async def suggest(self, context):
        raise NotImplementedError("Structured suggestion adapter is not implemented")
