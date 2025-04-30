function print_hook(fig, filename, format)
    % Default format handling
    if nargin < 3
        print(fig, filename, '-dpng'); % Default to PNG
    else
        print(fig, filename, format);
    end
    
    % Get the call stack
    stack = dbstack('-completenames');
    
    % Check if there is a caller (the second element in the stack)
    if length(stack) > 1
        callerFile = stack(2).file;  % The file that called this function
        % Call the Python script to track metadata
        track_figure_metadata_python(fig, callerFile);
        fprintf('print_hook was called from file: %s\n', callerFile);
    else
        fprintf('print_hook was called from the command line or has no caller.\nWARNING: METADATA NOT TRACKED FOR %s\n', fig);
    end
end
