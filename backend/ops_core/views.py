from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ops_core.services.ollama_service import OPSOllamaService
from ops_core.services.automation_service import OPSAutomationService
from ops_core.services.scraping_service import OPSScrapingService

ollama_service = OPSOllamaService()
automation_service = OPSAutomationService()
scraping_service = OPSScrapingService()

class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status": "online",
            "system": "O.P.S. (Over-Engineered Programmed System)",
            "version": "0.1.0",
            "tri_models": {
                "router": ollama_service.router_model,
                "reasoning": ollama_service.reasoning_model,
                "coding": ollama_service.coding_model
            }
        })

class IntentRouterView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt", "")
        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.route_request(prompt)
        return Response(result)

class PlanReasoningView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt", "")
        context = request.data.get("context", None)
        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.generate_plan(prompt, context)
        return Response(result)

class CodeSynthesizerView(APIView):
    def post(self, request):
        task = request.data.get("task", "")
        tool_name = request.data.get("tool_name", "code_editor")
        if not task:
            return Response({"error": "Task parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.generate_code_or_tool_params(task, tool_name)
        return Response(result)

class OrchestrationView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt", "")
        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.orchestrate_pipeline(prompt)
        return Response(result)

class WebScraperView(APIView):
    def post(self, request):
        url = request.data.get("url", "")
        if not url:
            return Response({"error": "URL parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = scraping_service.scrape_url(url)
        return Response(result)

class AutomationDispatcherView(APIView):
    def post(self, request):
        action_type = request.data.get("type", "dom")  # 'dom' or 'gui'
        action = request.data.get("action", "")
        
        if action_type == "dom":
            selector = request.data.get("selector", "")
            url = request.data.get("url", "")
            res = automation_service.execute_dom_action(action, selector, url=url)
        else:
            x = request.data.get("x", 0)
            y = request.data.get("y", 0)
            text = request.data.get("text", "")
            res = automation_service.execute_gui_action(action, x, y, text)
            
        return Response(res)
