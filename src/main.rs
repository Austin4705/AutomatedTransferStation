
use dotenv::dotenv;
use opencv::{
    Result,
    preslude::*,
    videoio,
    highgui,
}


fn main() -> Result<()>{
    dotenv().ok();
    let envVar: bool = std::env::var("sim_test").unwrap().parse::<bool>().unwrap();

    let cam = videoio::VideoCapture::new(0, videoio::CAP_ANY)?;
    highgui::named_window("window", highgui::WINDOW_FULLSCREEN)?;
    let frame = Mat::defualt();
    cam.read(&mut frame)?;
    highgui::imshow("window", &frame)?;
    highgui::wait_key(0)?;

    Ok(())
}