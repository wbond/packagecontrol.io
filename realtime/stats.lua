local server = require 'resty.websocket.server'
local fetch_stats = require 'fetch_stats'

-- Set up websocket server
local wb, err = server:new{
    timeout = 15000,
    max_payload_len = 65535
}
if not wb then
    ngx.say('Error connecting to stats server')
    return ngx.exit(444)
end


while true do
    local data, typ, err = wb:recv_frame()

    if wb.fatal then
        ngx.log(ngx.ERR, 'Websocket error receiving frame: ', err)
        return ngx.exit(444)
    end

    if not data then
        local bytes, err = wb:send_ping()
        if not bytes then
            ngx.log(ngx.ERR, 'Websocket error sending ping: ', err)
            return ngx.exit(444)
        end

    elseif typ == 'close' then
        break

    elseif typ == 'ping' then
        local bytes, err = wb:send_pong()
        if not bytes then
            ngx.log(ngx.ERR, 'Websocket error sending pong: ', err)
            return ngx.exit(444)
        end

    elseif typ == 'pong' then
        -- no op

    elseif typ == 'text' then
        if data == 'full' then
            output = fetch_stats(0)
        elseif data:sub(1, 5) == 'since' then
            only_since = tonumber(data:sub(7))
            output = fetch_stats(only_since)
        end

        local bytes, err = wb:send_text(output)
        if not bytes then
            ngx.log(ngx.ERR, 'Websocket error sending text: ', err)
            return ngx.exit(444)
        end

    end
end
wb:send_close()
