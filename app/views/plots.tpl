% from os.path import realpath


% if len(data) == 3:
%   plt_lst = data[2]

% if not plt_lst[0].endswith('.png'):  # No passes found, display that message
    <div>
        <p>{{plt_lst[0]}}</p>
    </div>
% else:
    % for plt in plt_lst:
        <div class="my-2">
        <img src="{{plt}}" class="img-fluid" alt="Responsive image">
        </div>
    % end
% end

