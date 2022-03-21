use clap::{App, Arg};
use futures::prelude::*;
use zenoh::config::Config;
use zenoh::prelude::*;
use zenoh::query::*;
use zenoh::queryable;
use std::time::{Duration, Instant};
use std::{thread, time};
use std::mem;
use rand::prelude::*;

use std::error::Error;
use csv::Writer;

#[async_std::main]
async fn main() {
    // initiate logging
    env_logger::init();

    let (config, selector, target,peers,getters,delay) = parse_args();

    let session = zenoh::open(config).await.unwrap();
    let init = time::Duration::from_secs(3);
    thread::sleep(init);
    let mut rng = rand::thread_rng();
    loop{
        let d = time::Duration::from_micros(delay.try_into().unwrap());
        thread::sleep(d);
        let kind = queryable::ALL_KINDS;
        let target = Target::All;
        let s = QueryTarget { kind,target  };
        let zo = rng.gen_range(1..=peers.parse().unwrap());
        let key_expr = format!("/sdn/**/hosts/{}",zo);
        let now = Instant::now();
        let mut replies = session.get(&key_expr).target(s).await.unwrap();
        let el = now.elapsed().as_micros();
        let mut x = 0;
        
        if let Some(reply) = replies.next().await {

             x = mem::size_of_val(&reply.data.value.payload.contiguous());
            // print!("res:  {:?}",String::from_utf8_lossy(&reply.data.value.payload.contiguous()));

        }
        println!("{},{},{},{},{:?}",&getters,&peers,delay,x,el);
    }
    
    
}

fn parse_args() -> (Config, String, QueryTarget, String, String, i32) {
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
    (config, selector, QueryTarget { kind, target },peers,getters,delay.parse().unwrap())
}