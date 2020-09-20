select 
                a.schedule_id as `生產序號`
                , concat(demands_id, a.crop_id, supplier_id) as `作物編號`
                , sowing_date as `播種日期`
                , require_date as `出貨日期`
                , b.`name` as `品種名稱`
                , d.`name` as `客戶名稱`
                , sum(c.piece) * 96 as `播種數量`
                , (sum(c.germination_cnt)+(case when add_ger_cnt is not null then add_ger_cnt else 0 end)) as `發芽數量`
                , (sum(c.germination_cnt)+(case when add_ger_cnt is not null then add_ger_cnt else 0 end)) / (sum(c.piece) * 96) as `發芽率`
                from crop_schedule a
                inner join crop_name b on b.crop_id = a.crop_id
                inner join process c on a.schedule_id = c.schedule_id
                inner join customer d on d.cust_id = a.cust_id
                left join (artificial_judgment
	                select 
	                c.schedule_id
	                , sum(a.judge_result) as add_ger_cnt
	                from artificial_judgment a
	                inner join sponge b on a.sponge_id = b.sponge_id
	                inner join process c on b.process_id = c.process_id
	                group by  c.schedule_id
                ) e on e.schedule_id = a.schedule_id
                where a.sowing_date >= '2020-07-12' and a.sowing_date <= '2020-07-14'
                group by a.schedule_id
                , concat(demands_id, a.crop_id, supplier_id)
                , sowing_date
                , require_date
                , b.`name`
                order by a.schedule_id;