//
// Copyright (c) 2017, 2020 ADLINK Technology Inc.
//
// This program and the accompanying materials are made available under the
// terms of the Eclipse Public License 2.0 which is available at
// http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
// which is available at https://www.apache.org/licenses/LICENSE-2.0.
//
// SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
//
// Contributors:
//   ADLINK zenoh team, <zenoh@adlink-labs.tech>
//

#![recursion_limit = "256"]

use async_std::task::sleep;
use clap::{App, Arg};
use futures::prelude::*;
use futures::select;
use std::collections::HashMap;
use std::time::Duration;
use zenoh::config::Config;
use zenoh::prelude::*;
use zenoh::queryable::STORAGE;
use zenoh::utils::key_expr;
use rand::prelude::*;


#[async_std::main]
async fn main() {
    // initiate logging
    env_logger::init();
    



    let (config, key_expr, zone) = parse_args();

    let mut stored: HashMap<String, Sample> = HashMap::new();

    let session = zenoh::open(config).await.unwrap();

    let mut subscriber = session.subscribe(&key_expr).await.unwrap();

    let mut queryable = session.queryable(&key_expr).kind(STORAGE).await.unwrap();
    let mut rng = rand::thread_rng();

    session.put(&key_expr, format!("{{'zone':'zone{}','ip':'{}.{}.{}.{}'}}",zone,rng.gen_range(0..255),rng.gen_range(0..255),rng.gen_range(0..255),rng.gen_range(0..255))).await.unwrap();

    
    loop {
        select!(
            sample = subscriber.next() => {
                let sample = sample.unwrap();
                
                if sample.kind == SampleKind::Delete {
                    stored.remove(&sample.key_expr.to_string());
                } else {
                    stored.insert(sample.key_expr.to_string(), sample);
                }
            },

            query = queryable.next() => {
                let query = query.unwrap();
                for (stored_name, sample) in stored.iter() {
                    if key_expr::intersect(query.selector().key_selector.as_str(), stored_name) {
                        query.reply(sample.clone());
                    }
                }
            }
        );
    }
}

fn parse_args() -> (Config, String, String) {
    let args = App::new("zenoh storage example")
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
            Arg::from_usage("-k, --key=[KEYEXPR] 'The selection of resources to store'")
                .default_value("/demo/example/**"),
        )
        .arg(Arg::from_usage(
            "-c, --config=[FILE]      'A configuration file.'",
        ))
        .arg(Arg::from_usage(
            "--no-multicast-scouting 'Disable the multicast-based scouting mechanism.'",
        ))
        .arg(Arg::from_usage(
            "-z, --zone==[ZONE] 'Disable the multicast-based scouting mechanism.'",
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
       
        let x = args.value_of("connect").unwrap();
        let y = x.parse::<i32>().unwrap();
        let mut getters = Vec::new();
        for i in 1..=y{
            getters.push(format!("tcp/0.0.0.0:{}",32769+i).parse().unwrap());
        }
        print!("{:?}",&getters);
        config
            .connect
            .endpoints
            .extend(getters)
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

    
    let zone = args.value_of("zone").unwrap().to_string();
    let key_expr = format!("/sdn/zone{}/hosts/{}",zone,zone);

    (config, key_expr, zone)
}