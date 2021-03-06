use clap::{App, Arg};
use futures::prelude::*;
use rand::prelude::*;
use std::mem;
use std::time::{Duration, Instant};
use std::{thread, time};
use zenoh::config::Config;
use zenoh::prelude::*;
use zenoh::query::*;
use zenoh::queryable;
use zenoh::publication::CongestionControl;

use zenoh::prelude::config::WhatAmI;

use csv::Writer;
use std::error::Error;

#[async_std::main]
async fn main() {
    // initiate logging
    env_logger::init();

    let (config, selector, target, peers, getters, delay, size) = parse_args();

    let session = zenoh::open(config).await.unwrap();
    let init = time::Duration::from_secs(10);
    async_std::task::sleep(init);
    let mut rng = rand::thread_rng();

    loop {
        let query_consolidation = QueryConsolidation::Manual(ConsolidationStrategy::none());

        let d = time::Duration::from_micros(delay.try_into().unwrap());
        async_std::task::sleep(d).await;
        let kind = queryable::ALL_KINDS;
        let target = Target::All;
        let s = QueryTarget { kind, target };
        //let zo = rng.gen_range(1..=peers.parse().unwrap());
        //let key_expr = format!("/sdn/**/hosts/{}", zo);
        let key_expr = "/sdn/**/hosts/1".to_string(); // /sdn/zone{n}/hosts/1
        let now = Instant::now();
        let mut replies = session.get(&key_expr).consolidation(query_consolidation).target(s).await.unwrap();
        let mut x = 0;
        let mut flag = 0;
        let mut first = 0;
        while let Some(reply) = replies.next().await {
            
            let el = now.elapsed().as_micros();
            if reply.data.value.payload.contiguous().len() > 0 {
                if flag == 0 {
                    first = now.elapsed().as_micros();
                    flag = 1;
                }   
                //println!("{},{},{},{},{},{:?}", &getters, &peers, delay, size, x, el);
                //x = 1;
                //print!("res:  {:?}",String::from_utf8_lossy(&reply.data.value.payload.contiguous()));
            }
        }
        if flag == 1{
            let el2 = now.elapsed().as_micros();
            println!("{},{},{},{},{},{:?}", &getters, &peers, delay, size, x, el2-first);
        }
        
        //println!("{},{},{},{},{},{:?}",&getters,&peers,delay,size,x,el);
    }
}

fn parse_args() -> (Config, String, QueryTarget, String, String, i32, usize) {
    let args = App::new("zenoh query example")
        .arg(
            Arg::from_usage("-m, --mode=[MODE]  'The zenoh session mode (peer by default).")
                .possible_values(&["peer", "client"]),
        )
        .arg(Arg::from_usage(
            "-e, --connect=[ENDPOINT]...   'Endpoints to connect to.'",
        ))
        .arg(Arg::from_usage(
            "-l, --listen=[ENDPOINT]...   'Endpoints to listen on.'",
        ))
        .arg(
            Arg::from_usage("-s, --selector=[SELECTOR] 'The selection of resources to query'")
                .default_value("/demo/example/**"),
        )
        .arg(
            Arg::from_usage("-k, --kind=[KIND] 'The KIND of queryables to query'")
                .possible_values(&["ALL_KINDS", "STORAGE", "EVAL"])
                .default_value("ALL_KINDS"),
        )
        .arg(
            Arg::from_usage("-t, --target=[TARGET] 'The target queryables of the query'")
                .possible_values(&["ALL", "BEST_MATCHING", "ALL_COMPLETE", "NONE"])
                .default_value("ALL"),
        )
        .arg(Arg::from_usage(
            "-c, --config=[FILE]      'A configuration file.'",
        ))
        .arg(Arg::from_usage(
            "--no-multicast-scouting 'Disable the multicast-based scouting mechanism.'",
        ))
        .arg(Arg::from_usage(
            "--peers=[NPEER] 'Disable the multicast-based scouting mechanism.'",
        ))
        .arg(Arg::from_usage(
            "--getters=[NPEER] 'Disable the multicast-based scouting mechanism.'",
        ))
        .arg(Arg::from_usage(
            "--delay=[NPEER] 'Disable the multicast-based scouting mechanism.'",
        ))
        .arg(Arg::from_usage(
            " --size==[ZONE] 'Disable the multicast-based scouting mechanism.'",
        ))
        .get_matches();

    let mut config = if let Some(conf_file) = args.value_of("config") {
        Config::from_file(conf_file).unwrap()
    } else {
        Config::default()
    };
    if let Some(Ok(mode)) = args.value_of("mode").map(|mode| mode.parse()) {
        config.set_mode(Some(mode)).unwrap();
    }
    if let Some(values) = args.values_of("connect") {
        config
            .connect
            .endpoints
            .extend(values.map(|v| v.parse().unwrap()))
    }
    if let Some(values) = args.values_of("listen") {
        config
            .listen
            .endpoints
            .extend(values.map(|v| v.parse().unwrap()))
    }
    if args.is_present("no-multicast-scouting") {
        config.scouting.multicast.set_enabled(Some(false)).unwrap();
    }

    let selector = "/sdn/**/hosts/1".to_string();

    let kind = match args.value_of("kind") {
        Some("STORAGE") => queryable::STORAGE,
        Some("EVAL") => queryable::EVAL,
        _ => queryable::ALL_KINDS,
    };

    let target = match args.value_of("target") {
        Some("BEST_MATCHING") => Target::BestMatching,
        Some("ALL_COMPLETE") => Target::AllComplete,
        Some("NONE") => Target::None,
        _ => Target::All,
    };
    let delay = args.value_of("delay").unwrap();
    let peers = args.value_of("peers").unwrap().to_string();
    let getters = args.value_of("getters").unwrap().to_string();
    let size = args.value_of("size").unwrap().parse::<usize>().unwrap();
    (
        config,
        selector,
        QueryTarget { kind, target },
        peers,
        getters,
        delay.parse().unwrap(),
        size,
    )
}
