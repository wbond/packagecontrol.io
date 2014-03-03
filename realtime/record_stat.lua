local redis = require 'resty.redis'

local record_stat = function(type)
    local red = redis:new()
    local ok, err = red:connect('unix:/tmp/redis.sock')
    if not ok then
        return
    end

    local step = 2
    local time = os.time()
    local bucket = time - (time % step)

    local key = type .. ':' .. bucket

    local res, err = red:incr(key)
    if res == 1 then
        red:expireat(key, time + 600)
    end
end

return record_stat
