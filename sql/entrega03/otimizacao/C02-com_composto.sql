SELECT order_id,order_date FROM nw.orders WHERE customer_id='VINET' AND order_date>=DATE '1996-01-01' AND order_date<DATE '1997-01-01' ORDER BY order_date,order_id;
