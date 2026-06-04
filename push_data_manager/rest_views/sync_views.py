from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from managers.sync_manager import SyncManager

_manager = SyncManager()


@csrf_exempt
@require_http_methods(["POST"])
def sync(request, ats_source: str):
    try:
        result = _manager.run_sync(ats_source)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_http_methods(["GET"])
def status(request, ats_source: str):
    try:
        result = _manager.get_status(ats_source)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
