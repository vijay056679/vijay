package com.vijay.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.ModelMap;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class MyController {
	
	@RequestMapping("/")
	public String name() {
		return "name";
		
	}
	@RequestMapping("/req1")
	public String fullName(@RequestParam String Fname,@RequestParam String Lname, ModelMap Model) {
		Model.put("k1",Fname);
		return "table";
		
	} 
	
	

}
