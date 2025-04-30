function print_hook(fig_or_filename, filename_or_format, varargin)
    if ishghandle(fig_or_filename)
        fig = fig_or_filename;
        filename = filename_or_format;
    else
        fig = gcf;
        filename = fig_or_filename;
        varargin = [{filename_or_format}, varargin];
    end

    if ~isabsolute_path(filename)
        filename = fullfile(pwd, filename);
    end

    print(fig, filename, varargin{:});

    stack = dbstack('-completenames');
    if length(stack) > 1
        callerFile = stack(2).file;
        track_figure_metadata_python(filename, callerFile);
        fprintf('print_hook was called from file: %s\n', callerFile);
    else
        fprintf('print_hook was called from the command line or has no caller.\nWARNING: METADATA NOT TRACKED FOR %s\n', filename);
    end
end

function tf = isabsolute_path(p)
    tf = startsWith(p, filesep) || ~isempty(regexp(p, '^[A-Za-z]:[\\/]', 'once'));
end
