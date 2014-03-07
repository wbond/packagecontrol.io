local redis = require 'resty.redis'

local fill_table = function(tab, size)
    if tab == nil then
        tab = {}
    end
    while #tab < size do
        table.insert(tab, 1, 0)
    end
    return tab
end

local table_end = function(tab, size)
    new_tab = {}
    last = #tab
    for i=size-1,0,-1 do
        new_tab[size-i] = tab[last-i]
    end
    return new_tab
end

local update_stats = function()
    local red = redis:new()
    local ok, err = red:connect('unix:/tmp/redis.sock')
    if not ok then
        ngx.log(ngx.ERR, 'Error connecting to redis: ', err)
        return
    end

    local step = 2
    local incremental_size = 3
    local full_size = 63

    local time = os.time()
    local goal = time - (time % step) - step

    local res, err = red:get('cached_through')
    local cached_through = tonumber(res) or 0

    -- Check if the caches need updating
    while cached_through < goal do
        res, err = red:get('cached_through')
        cached_through = tonumber(res)

        if cached_through then
            active_key = cached_through + step
        else
            active_key = goal - step
        end

        red:init_pipeline(3)
        res, err = red:get('channel:' .. active_key)
        res, err = red:get('usage:' .. active_key)
        res, err = red:get('web:' .. active_key)
        local results = red:commit_pipeline()

        local channel = tonumber(results[1]) or 0
        local usage = tonumber(results[2]) or 0
        local web = tonumber(results[3]) or 0

        -- Update the visit count lists
        red:init_pipeline(7)
        red:rpush('channel_list', channel)
        red:ltrim('channel_list', 0 - full_size, -1)

        red:rpush('usage_list', usage)
        red:ltrim('usage_list', 0 - full_size, -1)

        red:rpush('web_list', web)
        red:ltrim('web_list', 0 - full_size, -1)

        red:set('cached_through', tostring(active_key))
        red:commit_pipeline()

        -- Cache the rendered json so it is trivial to send to clients
        -- instead of rendering it on each request
        local channel_counts, err = red:lrange('channel_list', 0 - (full_size), -1)
        channel_counts = fill_table(channel_counts, full_size)
        local usage_counts, err = red:lrange('usage_list', 0 - (full_size), -1)
        usage_counts = fill_table(usage_counts, full_size)
        local web_counts, err = red:lrange('web_list', 0 - (full_size), -1)
        web_counts = fill_table(web_counts, full_size)

        full_json = string.format(
            '{"step":%s,"begin":%s,"end":%s,"channel":[%s],"usage":[%s],"web":[%s]}',
            step,
            active_key - ((full_size - 1) * step),
            active_key,
            table.concat(channel_counts, ","),
            table.concat(usage_counts, ","),
            table.concat(web_counts, ",")
        )
        red:set('full_json:' .. active_key, full_json)
        red:expireat('full_json:' .. active_key, time + 10)

        incremental_json = string.format(
            '{"step":%s,"begin":%s,"end":%s,"channel":[%s],"usage":[%s],"web":[%s]}',
            step,
            active_key - ((incremental_size - 1) * step),
            active_key,
            table.concat(table_end(channel_counts, incremental_size), ","),
            table.concat(table_end(usage_counts, incremental_size), ","),
            table.concat(table_end(web_counts, incremental_size), ",")
        )
        red:set('incremental_json:' .. active_key, incremental_json)
        red:expireat('incremental_json:' .. active_key, time + 10)

        cached_through = active_key
    end
end

return update_stats
