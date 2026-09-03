"""Azure Functions entry point placeholder.

The same MCP handler is deployable behind an Azure Functions HTTP trigger. The
dependency-free local server remains the canonical offline demo.
"""
try:
    import azure.functions as func
except ImportError:  # local-only environments do not need the Azure SDK
    func = None

def main(req):
    if func is None:
        raise RuntimeError("Install Azure Functions dependencies to use this entry point")
    return func.HttpResponse("Configure the Functions HTTP trigger to forward MCP requests.", status_code=501)
