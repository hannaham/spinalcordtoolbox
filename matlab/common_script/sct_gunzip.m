function sct_gunzip(varargin)
try 
    gunzip(varargin{1:2})
catch
    if nargin>1
        copyfile(varargin{1},varargin{2})
    end
end

if nargin==3
    cd(varargin{2})
    movefile([sct_tool_remove_extension(varargin{1},0) '.nii'],varargin{3});
    cd ../
end
