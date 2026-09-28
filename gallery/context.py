from .models import Painting, SiteProfile


def profile(request):
    return {"profile": SiteProfile.load(), "featured": Painting.objects.first()}
