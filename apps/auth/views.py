from django.views.generic import TemplateView


class AuthView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = (self, super().get_context_data(**kwargs))

        # Update the context
        context.update(
            {
                "layout_path": ("layout_blank.html", context),
            }
        )

        return context
