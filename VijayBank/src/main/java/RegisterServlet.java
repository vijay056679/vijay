

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


@WebServlet("/RegisterServlet")
public class RegisterServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
    
    public RegisterServlet() {
        super();
        // TODO Auto-generated constructor stub
    }

	
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		PrintWriter pw=response.getWriter();
		
		String username=request.getParameter("username");
		String password=request.getParameter("password");
		
		try
		{
			Class.forName("oracle.jdbc.driver.OracleDriver");
			String url="jdbc:oracle:thin:@localhost:1521:xe";
			Connection con=DriverManager.getConnection(url,"system","056679");
			
			String sql="insert into Login values(?,?)";
			PreparedStatement ps=con.prepareStatement(sql);
			
			ps.setString(1, username);
			ps.setString(2, password);
			
			int count=ps.executeUpdate();
			ps.close();
			con.close();
			if(count>0)
			{
				pw.println("<h2>Registered Successfully,Login now</h2>");
				response.setContentType("text/html");
				RequestDispatcher rd=request.getRequestDispatcher("Login.html");
				rd.include(request,response);
			}
			else
			{
				pw.println("<h2>Failed , Try Again</h2>");
				response.setContentType("text/html");
				RequestDispatcher rd=request.getRequestDispatcher("Registration.html");
				rd.include(request,response);
			}
				
		}
		catch(Exception e)
		{
			e.getMessage();
		}
	}

}

