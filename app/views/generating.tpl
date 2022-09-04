%# This HTMX will replace the 'info' div on the main_view template once 'Generate Predicts' is clicked
%# Once it loads, it will automatically call '/generate' as per hx-trigger
%# The 'generate' endpoint will return plot contents and reload only the 'info' div, not entire page

<div hx-get="/generate" hx-include="#inputs" hx-trigger="load delay:0ms">
    <div class="d-flex">
        <h6>Generating predicts...</h6>
        <span class="spinner-grow spinner-grow-sm text-light mx-4" role="status"></span>
    </div>

</div>
