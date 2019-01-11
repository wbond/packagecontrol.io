local redis = require 'resty.redis'

local fetch_stats = function(only_since)
    -- Connect to redis
    local red = redis:new()
    local ok, err = red:connect('unix:/var/run/redis/redis.sock')
    if not ok then
        ngx.log(ngx.ERR, 'Error connecting to redis: ', err)
        return
    end

    local step = 2
    local incremental_size = 3
    local time = os.time()
    local bucket = time - (time % step) - (2 * step)
    local json

    if only_since and only_since >= bucket - (incremental_size * step) then
        json, err = red:get('incremental_json:' .. bucket)
        return json
    end

    json, err = red:get('full_json:' .. bucket)
    return json
end

return fetch_stats
