from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from .services import GlobalSearchService

class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'search/results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        
        # Max length validation (configurable/reasonable limit)
        if len(query) > 100:
            query = query[:100]
            
        context['query'] = query
        
        if not query:
            context['empty_query'] = True
            context['has_results'] = False
            return context
            
        context['empty_query'] = False
        results = GlobalSearchService.search(self.request.user, query, limit_per_category=10)
        
        context['results'] = results
        
        # Determine if no results
        has_results = any(len(category_items) > 0 for category_items in results.values())
        context['has_results'] = has_results
        
        return context
