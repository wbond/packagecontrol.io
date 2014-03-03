local lock = require 'resty.lock'
local timer = ngx.timer.at
local update_stats = require 'update_stats'

local locks = lock:new('locks')

local update_cache
update_cache = function(premature)
    if premature then
        return
    end

    local elapsed, err = locks:lock("update_lock")
    if not elapsed then
        ngx.log(ngx.ERR, 'Error obtaining lock: ', err)
        return
    end

    update_stats()
    
    local ok, err = locks:unlock()
    if not ok then
        ngx.log(ngx.ERR, 'Error unlocking: ', err)
        return
    end
    
    local ok, err = timer(1, update_cache)
    if not ok then
        ngx.log(ngx.ERR, 'Error creating timer: ', err)
        return
    end
end

local ok, err = timer(1, update_cache)
if not ok then
    ngx.log(ngx.ERR, 'Error creating timer: ', err)
    return
end
