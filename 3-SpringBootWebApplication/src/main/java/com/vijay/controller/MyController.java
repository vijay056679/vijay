package com.vijay.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
public class MyController {

   
	@RequestMapping("/")
	public String homePage() {
		return "index";
	}
	@RequestMapping("Contacturl")
		public String contactPage() {
			return "Contact";
		}
	@RequestMapping("Loginurl")
		public String loginPage() {
			return "Login";
			
		}
	@RequestMapping("Regurl")
		public String registerPage() {
			return "Reg";
		}
}
