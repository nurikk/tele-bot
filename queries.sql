select
    full_name,
    count(*)
from
    card_requests r
    left join users u on r.user = u.id
GROUP BY
    1
ORDER BY
    2 DESC;